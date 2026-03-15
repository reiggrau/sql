# SQL Trainer

A Python + FastAPI backend for practicing SQL queries through interactive API endpoints.
Built using PostgreSQL and raw SQL.

## Getting started

### 0. Prerequisites

- Python 3.13+
- PostgreSQL

### 1. Clone and set up the virtual environment

```bash
git clone <repo-url>
cd sql
```

### 2. Create & activate the virtual environment

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows ONLY! In macOs & Linux use: source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/sql_training
```

### 4. Create and seed the database

```bash
psql -U postgres -c "CREATE DATABASE sql_training;"
python -m scripts.seed
```

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs .

## Tech stack

PostgreSQL - Relational database
psycopg - PostgreSQL driver (raw SQL)
FastAPI - Web framework with interactive /docs
Uvicorn - ASGI server  
pydantic-settings - Environment config
Alembic - Database migrations
