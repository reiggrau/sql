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
