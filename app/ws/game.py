from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from app.core.settings import settings
from app.db.connection import fetch_one
from app.ws.manager import manager

router = APIRouter()


def authenticate_ws(token: str) -> dict | None:
    """Validate a JWT token and return the player dict, or None."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        player_id = payload.get("sub")
        if player_id is None:
            return None
    except JWTError:
        return None

    return fetch_one(
        "SELECT id, username FROM players WHERE id = %s;",
        (int(player_id),),
    )


@router.websocket("/ws/games/{game_id}")
async def game_ws(ws: WebSocket, game_id: str, token: str = Query(...)):
    # --- Auth ---
    player = authenticate_ws(token)
    if not player:
        await ws.close(code=4001, reason="Invalid or expired token")
        return

    # --- Join or create ---
    game = manager.get_game(game_id)

    if game is None:
        # No game with this ID exists → create a new lobby
        game = manager.create_game(game_id, player, ws)
        await ws.send_json({
            "type": "waiting",
            "message": "Lobby created. Waiting for opponent...",
            "game_id": game_id,
            "color": "Yellow",
        })

    elif not game.is_full:
        # Lobby exists and needs a second player → join
        if player["id"] == game.host["id"]:
            await ws.send_json({"type": "error", "message": "You are already the host"})
            await ws.close()
            return

        game.add_guest(player, ws)
        await game.broadcast({
            "type": "start",
            "message": "Game started!",
            "game_id": game_id,
            "host": game.host["username"],
            "guest": game.guest["username"],
            "turn": game.host["username"],
        })

    else:
        # Game is full → reject
        await ws.send_json({"type": "error", "message": "Game is full"})
        await ws.close()
        return

    # --- Relay loop ---
    try:
        while True:
            data = await ws.receive_json()

            # Forward the message to the other player
            other = game.other_id(player["id"])
            if other is None:
                await ws.send_json({
                    "type": "error",
                    "message": "Waiting for opponent",
                })
                continue

            # Attach the sender's info and relay
            data["player"] = player["username"]
            await game.send_to(other, data)

    except WebSocketDisconnect:
        # Notify the other player and clean up
        game.connections.pop(player["id"], None)
        if game.connections:
            for remaining_ws in game.connections.values():
                await remaining_ws.send_json({
                    "type": "opponent_left",
                    "message": f"{player['username']} disconnected",
                })
        manager.remove_game(game_id)
