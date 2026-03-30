"""Router for lobby-related endpoints."""

from fastapi import APIRouter
from app.ws.manager import manager

router = APIRouter(prefix="/lobbies", tags=["lobbies"])


@router.get("", summary="List open lobbies")
def list_lobbies():
    """List all open lobbies."""
    return manager.get_open_lobbies()
