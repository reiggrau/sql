"""This module defines the API endpoints for application-related operations."""

from fastapi import APIRouter
from app.db.connection import fetch_one, fetch_all

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/", summary="Get all applications")
def get_applications() -> list[dict]:
    """Get all applications."""
    sql = "SELECT * FROM applications;"
    return fetch_all(sql)


@router.get("/{application_id}", summary="Get application by id")
def get_application(application_id: int) -> dict | None:
    """Get an application by its ID."""
    sql = "SELECT * FROM applications WHERE id = %s;"
    return fetch_one(sql, (application_id,))
