"""Seed the database with initial data for testing and development purposes."""

import psycopg
from app.core.settings import settings

SCHEMA = """
DROP TABLE IF EXISTS moves, games, players;

CREATE TABLE players (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(20)  UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);
"""

SEED = """
INSERT INTO players (username, password_hash) VALUES
	('Player1', 'pass1'),
	('Player2', 'pass2'),
    ('Player3', 'pass3'),
    ('Player4', 'pass4');
"""


def main():
    """Seed the database with initial data."""
    with psycopg.connect(settings.database_url) as conn:
        conn.execute(SCHEMA)
        conn.execute(SEED)
        conn.commit()  # Commit the transaction to save changes to the database
    print("Database seeded successfully.")


if __name__ == "__main__":
    main()
