"""This module defines the API endpoints for player-related operations."""

from fastapi import APIRouter, HTTPException
from app.db.connection import fetch_one, fetch_all

router = APIRouter(prefix="/players", tags=["players"])
