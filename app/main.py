"""Main application file for the SQL API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.health import router as health_router
from .routers.db_check import router as db_check_router
from .routers.auth import router as auth_router
from .routers.players import router as players_router
from .routers.lobbies import router as lobbies_router
from .ws.game import router as game_ws_router

app = FastAPI(title="Connect4 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"], summary="Root endpoint")
def root() -> dict:
    """Root endpoint to check if the API is running."""
    return {"status": "ok", "message": "API is running!"}


app.include_router(health_router)
app.include_router(db_check_router)
app.include_router(auth_router)
app.include_router(players_router)
app.include_router(lobbies_router)
app.include_router(game_ws_router)
