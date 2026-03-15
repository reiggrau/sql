"""Database connection check endpoint."""


from fastapi import APIRouter
from app.db.connection import fetch_one


router = APIRouter(prefix="/db", tags=["database"])


@router.get("/check", summary="Database connection check")
def db_check() -> dict:
    """Endpoint to check database connectivity."""
    result = fetch_one("SELECT 1 AS connected;")
    return {"database": "connected", "result": result}
