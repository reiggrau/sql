"""Authentication utilities for the FastAPI application, including JWT token generation and validation."""

from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.core.settings import settings
from app.db.connection import fetch_one

security_scheme = HTTPBearer()


def create_access_token(player_id: int) -> str:
    """Generates a JWT access token for the given player ID."""
    expire = datetime.now(timezone.utc) + \
        timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(player_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_current_player(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """Retrieves the current player based on the provided JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        player_id = payload.get("sub")
        if player_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
    except JWTError as exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exception

    player = fetch_one(
        "SELECT id, username, created_at FROM players WHERE id = %s;",
        (int(player_id),),
    )
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Player not found",
        )
    return player
