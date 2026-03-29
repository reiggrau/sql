"""Database connection and query execution utilities for the SQL application."""

import psycopg
from psycopg.rows import dict_row
from app.core.settings import settings


def get_connection():
    """Get a connection to the PostgreSQL database."""
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def fetch_one(sql: str, params: tuple | None = None) -> dict | None:
    """Execute a SQL query and return a single result as a dictionary."""
    with get_connection() as conn:  # Ensure the connection is closed after use
        with conn.cursor() as cur:  # Ensure the cursor is closed after use
            cur.execute(sql, params or ())  # Execute the SQL query
            return cur.fetchone()  # Fetch a single result and return it


def fetch_all(sql: str, params: tuple | None = None) -> list[dict]:
    """Execute a SQL query and return all results as a list of dictionaries."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def execute(sql: str, params: tuple | None = None) -> dict | None:
    """Execute a write query (INSERT/UPDATE/DELETE) and return the result."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.fetchone()
