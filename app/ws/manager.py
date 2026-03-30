"""Manager for WebSocket connections and game state in Connect4."""

from fastapi import WebSocket


class Game:
    """Represents a single game room (lobby or in-progress)."""

    def __init__(self, game_id: str, host: dict, ws: WebSocket):
        """Initialize a new game with a host player and their WebSocket."""
        self.game_id = game_id
        self.host = host            # player dict from get_current_player
        self.guest = None           # filled when someone joins
        self.connections: dict[int, WebSocket] = {host["id"]: ws}

    @property
    def is_full(self) -> bool:
        """Returns True if both host and guest are present."""
        return self.guest is not None

    def add_guest(self, player: dict, ws: WebSocket):
        """Adds a guest player to the game."""
        self.guest = player
        self.connections[player["id"]] = ws

    async def broadcast(self, message: dict):
        """Send a JSON message to all connected players."""
        for ws in self.connections.values():
            await ws.send_json(message)

    async def send_to(self, player_id: int, message: dict):
        """Send a JSON message to a specific player."""
        ws = self.connections.get(player_id)
        if ws:
            await ws.send_json(message)

    def other_id(self, player_id: int) -> int | None:
        """Return the other player's ID, or None if solo."""
        if player_id == self.host["id"] and self.guest:
            return self.guest["id"]
        if self.guest and player_id == self.guest["id"]:
            return self.host["id"]
        return None


class ConnectionManager:
    """Tracks all lobbies and active games in memory."""

    def __init__(self):
        self.games: dict[str, Game] = {}  # game_id -> Game

    def create_game(self, game_id: str, host: dict, ws: WebSocket) -> Game:
        """Create a new game lobby with the given host player and WebSocket."""
        game = Game(game_id, host, ws)
        self.games[game_id] = game
        return game

    def get_game(self, game_id: str) -> Game | None:
        """Retrieve a game by its ID, or None if it doesn't exist."""
        return self.games.get(game_id)

    def remove_game(self, game_id: str):
        """Remove a game by its ID."""
        self.games.pop(game_id, None)

    def get_open_lobbies(self) -> list[dict]:
        """Return all games that are waiting for a second player."""
        return [
            {"game_id": g.game_id, "host": g.host["username"]}
            for g in self.games.values()
            if not g.is_full
        ]


manager = ConnectionManager()
