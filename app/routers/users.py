"""This module defines the API endpoints for user-related operations."""

from fastapi import APIRouter, HTTPException
from app.db.connection import fetch_one, fetch_all

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", summary="Get all users")
def get_users() -> list[dict]:
    """Get all users."""
    sql = """--sql
    SELECT * FROM users;
    """
    return fetch_all(sql)


@router.get("/companies", summary="Get users with company info")
def get_users_with_company_info() -> list[dict]:
    """Get all users along with their company information."""
    sql = """--sql
        SELECT u.id, u.name, u.email, c.id AS company_id, c.name AS company_name
        FROM users u
        LEFT JOIN companies c ON u.company_id = c.id;
    """
    return fetch_all(sql)


@router.get("/employed", summary="Get employed users")
def get_employed_users_with_company_and_application_date() -> list[dict]:
    """Get all users who are currently employed,
    along with their company information,
    and the date they applied for the company."""
    sql = """--sql
        SELECT u.id, u.name, u.email, c.id AS company_id, c.name AS company_name, a.applied_at
        FROM users u
        INNER JOIN applications a ON u.id = a.user_id
        INNER JOIN companies c ON a.company_id = c.id
        WHERE a.status = 'accepted'
        ORDER BY a.applied_at DESC;
    """
    return fetch_all(sql)


@router.get("/{user_id}", summary="Get user by id")
def get_user(user_id: int) -> dict | None:
    """Get a user by their ID."""
    sql = """--sql
    SELECT * FROM users WHERE id = %s;
    """
    user = fetch_one(sql, (user_id,))
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User {user_id} not found")
    return user


@router.get("/email/{email}", summary="Get user by email")
def get_user_by_email(email: str) -> dict | None:
    """Get a user by their email."""
    sql = """--sql
    SELECT * FROM users WHERE email = %s;
    """
    user = fetch_one(sql, (email,))
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with email {email} not found")
    return user
