"""Database connection and query execution utilities for the SQL application."""

import psycopg
from psycopg.rows import dict_row
from app.core.settings import settings


def get_connection():
    """Get a connection to the PostgreSQL database."""
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def fetch_one(sql: str, params: tuple | None = None) -> dict | None:
    """Execute a SQL query and return a single result as a dictionary."""
    with get_connection() as connection:  # Ensure the connection is closed after use
        with connection.cursor() as cursor:  # Ensure the cursor is closed after use
            cursor.execute(sql, params or ())  # Execute the SQL query
            return cursor.fetchone()  # Fetch a single result and return it


def fetch_all(sql: str, params: tuple | None = None) -> list[dict]:
    """Execute a SQL query and return all results as a list of dictionaries."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()


def execute(sql: str, params: tuple | None = None) -> dict | None:
    """Execute a write query (INSERT/UPDATE/DELETE) and return the result."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            connection.commit()
            return cursor.fetchone()
