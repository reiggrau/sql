"""Authentication router for player registration and login."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.db.connection import fetch_one, execute
from app.core.security import hash_password, verify_password
from app.core.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    """Request body for authentication endpoints."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Response model for authentication endpoints."""
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new player",
)
def register(body: AuthRequest):
    """Register a new player with a unique username and password."""
    existing = fetch_one(
        "SELECT id FROM players WHERE username = %s;", (body.username,)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    hashed = hash_password(body.password)
    player = execute(
        "INSERT INTO players (username, password_hash) VALUES (%s, %s) RETURNING id;",
        (body.username, hashed),
    )
    token = create_access_token(player["id"])
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get an access token",
)
def login(body: AuthRequest):
    """Authenticate a player and return an access token."""
    player = fetch_one(
        "SELECT id, password_hash FROM players WHERE username = %s;",
        (body.username,),
    )
    if not player or not verify_password(body.password, player["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(player["id"])
    return TokenResponse(access_token=token)
