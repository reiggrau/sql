# Connect4 Backend

The backend for a browser-based Connect 4 game. Handles player registration and login (JWT auth), game lobbies, move history, and real-time multiplayer via WebSockets.

Built with FastAPI, PostgreSQL (raw SQL via psycopg), and vanilla JavaScript on the frontend.

## Tech stack

| Tool                      | Role                                |
| ------------------------- | ----------------------------------- |
| Python 3.13+              | Language                            |
| FastAPI                   | Web framework (REST + WebSocket)    |
| Uvicorn                   | ASGI server                         |
| PostgreSQL                | Database                            |
| psycopg                   | PostgreSQL driver (raw SQL, no ORM) |
| pydantic-settings         | Environment config                  |
| passlib[bcrypt]           | Password hashing                    |
| python-jose[cryptography] | JWT creation and verification       |

## Getting started

### 1. Prerequisites

- Python 3.13+
- PostgreSQL running locally

### 2. Clone and set up

```bash
git clone <repo-url>
cd connect4/backend
```

### 3. Create and activate the virtual environment

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the `backend/` root:

```env
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/connect4
```

Generate a secure secret key with:

```bash
openssl rand -hex 32
```

### 5. Create and seed the database

```bash
psql -U postgres -c "CREATE DATABASE connect4;"
python -m scripts.seed
```

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs .

---

## Build guide

A step-by-step walkthrough of how this backend was built from scratch. Each step is self-contained and can be followed as a tutorial.

### Step 0 — Project setup

Before writing any application code, set up the Python project foundation.

**Create the project folder and virtual environment:**

```bash
mkdir connect4 && cd connect4
mkdir backend && cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # macOS / Linux
```

A virtual environment (`.venv/`) is an isolated Python installation for this project. Packages you install here won't interfere with other projects or your system Python. Always activate it before working on the project.

**Install the base dependencies:**

```bash
pip install fastapi uvicorn psycopg psycopg-binary pydantic-settings python-dotenv
```

| Package                      | Why                                                                                                                                                         |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fastapi`                    | The web framework. Handles routing, request validation, and auto-generates interactive docs at `/docs`.                                                     |
| `uvicorn`                    | The ASGI server that actually runs the FastAPI app. ASGI is the async equivalent of WSGI — it's the interface between the web server and the Python app.    |
| `psycopg` + `psycopg-binary` | PostgreSQL driver. Lets you execute raw SQL from Python. The `-binary` package includes pre-compiled C extensions so you don't need a C compiler installed. |
| `pydantic-settings`          | Loads environment variables (from `.env`) into a typed Python class.                                                                                        |
| `python-dotenv`              | Reads `.env` files. Used under the hood by pydantic-settings.                                                                                               |

**Create the initial folder structure:**

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── connection.py
│   └── routers/
│       ├── __init__.py
│       ├── health.py
│       └── db_check.py
├── scripts/
│   └── seed.py
├── .env
└── requirements.txt
```

Every `__init__.py` file is empty — they just tell Python that the folder is a package so imports like `from app.core.settings import settings` work.

**Create the `.env` file:**

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/connect4
```

This is the connection string for your local PostgreSQL. Format: `postgresql://USER:PASSWORD@HOST:PORT/DATABASE_NAME`. In production, your hosting provider will give you a different URL — you just swap it in `.env` without changing any code.

**`app/core/settings.py`** — loads environment variables into a typed config object:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
```

`BaseSettings` reads from environment variables first, then falls back to `.env`. The field name `database_url` matches `DATABASE_URL` in the env file (case-insensitive). If it's missing, the app crashes on startup with a clear error — fail fast.

**`app/db/connection.py`** — database query helpers:

```python
import psycopg
from psycopg.rows import dict_row
from app.core.settings import settings

def get_connection():
    return psycopg.connect(settings.database_url, row_factory=dict_row)

def fetch_one(sql: str, params: tuple | None = None) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

def fetch_all(sql: str, params: tuple | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
```

`row_factory=dict_row` makes psycopg return rows as dictionaries (`{"id": 1, "name": "alice"}`) instead of tuples. The `with` statements ensure connections and cursors are always properly closed, even if an error occurs. `params` uses `%s` placeholders to prevent SQL injection — never use f-strings or string concatenation with user input in SQL queries.

**`app/routers/health.py`** — a smoke test to verify the API is running:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", summary="Health check")
def health_check() -> dict:
    return {"status": "ok", "message": "API is healthy and running."}
```

**`app/routers/db_check.py`** — verifies database connectivity:

```python
from fastapi import APIRouter
from app.db.connection import fetch_one

router = APIRouter(prefix="/db", tags=["database"])

@router.get("/check", summary="Database connection check")
def db_check() -> dict:
    result = fetch_one("SELECT 1 AS connected;")
    return {"database": "connected", "result": result}
```

**`app/main.py`** — the entry point that wires everything together:

```python
from fastapi import FastAPI
from .routers.health import router as health_router
from .routers.db_check import router as db_check_router

app = FastAPI(title="Connect4 API", version="0.1.0")

@app.get("/", tags=["root"], summary="Root endpoint")
def root() -> dict:
    return {"status": "ok", "message": "API is running!"}

app.include_router(health_router)
app.include_router(db_check_router)
```

FastAPI uses `APIRouter` to organize endpoints into separate files. Each router is a mini-app that gets merged into the main `app` via `include_router()`. The `prefix` means all routes in `health.py` start with `/health`, keeping URLs tidy.

**Start the server and verify:**

```bash
uvicorn app.main:app --reload
```

`app.main:app` means "in the `app/main.py` file, use the `app` object". `--reload` watches for file changes and auto-restarts (dev only). Open http://127.0.0.1:8000/docs — you should see the interactive Swagger UI with your health and db check endpoints.

---

### Step 1 — Install auth dependencies

Install the two libraries needed for authentication:

```bash
pip install "passlib[bcrypt]" "python-jose[cryptography]"
```

| Package                     | Why                                                                                                                                                                                |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `passlib[bcrypt]`           | Password hashing library. bcrypt is the hashing algorithm — it's deliberately slow, which makes brute-force attacks impractical. The `[bcrypt]` extra installs the bcrypt backend. |
| `python-jose[cryptography]` | Creates and verifies JSON Web Tokens (JWTs). The `[cryptography]` extra gives it a fast C backend for signing operations.                                                          |

**Why two separate libraries?** They solve different problems:

- `passlib` turns a plain password into an irreversible hash for storage. You can verify a password against a hash, but you can never recover the original password from the hash.
- `python-jose` creates a signed token containing data (like a player ID). The token is not encrypted — anyone can read its contents — but only the server can create valid ones because only the server knows the `SECRET_KEY`.

---

### Step 2 — Update settings

Add authentication config to `.env`:

```env
# AUTH
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# DB
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/connect4
```

Generate a proper secret key:

```bash
openssl rand -hex 32
```

This outputs 64 hex characters (256 bits of randomness). Replace `your-secret-key-here` with the output. Anyone who knows this key can forge valid tokens, so never commit real keys to git — `.env` should be in `.gitignore`.

`HS256` (HMAC-SHA256) is the signing algorithm — it's symmetric, meaning the same key both signs and verifies. Fast, simple, and standard.

**Update `app/core/settings.py`** to load the new fields:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
```

The `= "HS256"` and `= 60` are defaults — if those env vars are missing, these values are used. `database_url` and `secret_key` have no defaults, so the app will crash with a validation error if they're missing. This is intentional: the app should not start without a database or a signing key.

---

### Step 3 — Create the `players` table and seed it

```python
import psycopg
from app.core.settings import settings

SCHEMA = """
DROP TABLE IF EXISTS moves, games, players;

CREATE TABLE players (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);
"""

SEED = """
INSERT INTO players (username, password_hash) VALUES
	('Alice', 'password1'),
	('Bob', 'password2'),
    ('Carol', 'password3'),
    ('Dave', 'password4'),
    ('Eve', 'password5');
"""

def main():
    with psycopg.connect(settings.database_url) as conn:
        conn.execute(SCHEMA)
        conn.execute(SEED)
        conn.commit()
    print("Database seeded successfully.")

if __name__ == "__main__":
    main()
```

**Key design decisions:**

- `SERIAL PRIMARY KEY` — auto-incrementing integer ID. PostgreSQL handles assigning the next value.
- `VARCHAR(20) UNIQUE NOT NULL` — usernames must be unique and can't be empty. 20 chars is generous but prevents abuse.
- `TEXT` for `password_hash` — bcrypt hashes are 60 characters, but `TEXT` avoids hardcoding a length that might change if you switch algorithms later.
- `DEFAULT NOW()` — PostgreSQL fills in the current timestamp automatically on insert.
- No `email` field — we're keeping auth simple with just username + password for now.

The `DROP TABLE IF EXISTS` line at the top wipes existing tables. The order matters: `moves` and `games` reference `players`, so they must be dropped first (we include them already for future steps). During development this is fine; in production you'd use migrations instead.

**Run it:**

```bash
psql -U postgres -c "CREATE DATABASE connect4;"
python -m scripts.seed
```

The `-m` flag runs `scripts/seed.py` as a module, which means Python resolves imports like `from app.core.settings import settings` correctly relative to the project root.

### Step 4 — Add a write helper

Add an `execute()` function to `db/connection.py` for INSERT/UPDATE/DELETE queries that commits and returns the result.

### Step 5 — Create `core/security.py`

Implement `hash_password()` and `verify_password()` using passlib's bcrypt context.

### Step 6 — Create `core/auth.py`

Implement `create_access_token()` for JWT creation and `get_current_player()` as a FastAPI dependency that protects routes by extracting and validating the Bearer token.

### Step 7 — Create `routers/auth.py`

Build `POST /auth/register` and `POST /auth/login` endpoints with Pydantic request/response models.

### Step 8 — Create `routers/players.py`

Build `GET /players/me` as a protected endpoint using the `get_current_player` dependency. Replaces the old `users.py` router.

### Step 9 — Update `main.py`

Remove old routers (companies, applications, users), wire in the new ones (auth, players), and add CORS middleware.

### Step 10 — Create the `games` and `moves` tables

Extend `scripts/seed.py` with tables for game sessions (`games`) and move history (`moves`).

### Step 11 — Create `routers/lobbies.py`

Build endpoints to create a game (`POST /lobbies`), list open games (`GET /lobbies`), and join a game (`POST /lobbies/{id}/join`).

### Step 12 — Create `routers/games.py`

Build endpoints to retrieve game history (`GET /games`) and full game state with moves (`GET /games/{id}`).

### Step 13 — Create `ws/manager.py`

Implement a `ConnectionManager` class that tracks active WebSocket connections per game room.

### Step 14 — Create `ws/game.py`

Build the WebSocket endpoint (`ws://host/ws/games/{game_id}?token=<JWT>`) with token authentication, move validation, turn enforcement, server-side win detection, and message broadcasting to both players.

### Step 15 — Freeze dependencies

Run `pip freeze > requirements.txt` to lock all package versions.

### Step 16 — Test the full flow

Register → login → create lobby → join → play via WebSocket → win → check game history.
