"""Health check endpoint for the API."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health check")
def health_check() -> dict:
    """Endpoint to check if the API is running."""
    return {"status": "ok", "message": "API is healthy and running."}
