"""Seed the database with initial data for testing and development purposes."""

import psycopg
from app.core.settings import settings

SCHEMA = """
DROP TABLE IF EXISTS applications, users, companies;

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
  	industry VARCHAR(50)
);

CREATE TABLE users (
	id SERIAL PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	email VARCHAR(150) UNIQUE NOT NULL,
	company_id INT REFERENCES companies(id),
	created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    company_id INT REFERENCES companies(id),
    status VARCHAR(20) DEFAULT 'pending',
    applied_at TIMESTAMP DEFAULT NOW()
);
"""

SEED = """
INSERT INTO companies (name, industry) VALUES
	('Acme Corp', 'Tech'),
    ('Globex', 'Finance'),
    ('Initech', 'Consulting'),
    ('Umbrella', 'Biotech');
    
INSERT INTO users (name, email, company_id) VALUES
	('Alice', 'alice@example.com', 1),
	('Bob', 'bob@example.com', 1),
    ('Carol', 'carol@example.com', 2),
    ('Dave', 'dave@example.com', 3),
    ('Eve', 'eve@example.com', NULL);

INSERT INTO applications (user_id, company_id, status) VALUES
	(1, 2, 'accepted'),
    (1, 3, 'pending'),
    (2, 2, 'rejected'),
    (3, 1, 'accepted'),
    (4, 1, 'pending'),
    (4, 4, 'accepted'),
    (5, 1, 'pending'),
    (5, 2, 'pending'),
    (5, 3, 'rejected');
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
