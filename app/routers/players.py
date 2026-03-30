"""This module defines the API endpoints for player-related operations."""

from fastapi import APIRouter, Depends
from app.core.auth import get_current_player

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/me", summary="Get my profile")
def get_me(player: dict = Depends(get_current_player)):
    """Endpoint to retrieve the current player's profile information."""
    return player
