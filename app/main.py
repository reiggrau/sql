"""Main application file for the SQL API."""

from fastapi import FastAPI
from .routers.health import router as health_router
from .routers.db_check import router as db_check_router
from .routers.players import router as players_router


app = FastAPI(
    title="SQL Trainer API",
    version="0.1.0",
)


@app.get("/", tags=["root"], summary="Root endpoint")
def root() -> dict:
    """Root endpoint to check if the API is running."""
    return {"status": "ok", "message": "API is running!"}


app.include_router(health_router)  # Include the health check router
app.include_router(db_check_router)  # Include the database check router
app.include_router(players_router)  # Include the players router
