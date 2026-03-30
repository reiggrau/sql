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
| bcrypt                    | Password hashing                    |
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

### Step 0 — Project initialization

Create the project folder and set up a Python virtual environment.

```bash
mkdir connect4 && cd connect4
mkdir backend && cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # macOS / Linux
```

A virtual environment (`.venv/`) is an isolated Python installation for this project. Packages you install here won't interfere with other projects or your system Python. Always activate it before working on the project.

Create the initial folder structure:

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

---

### Step 1 — Install base dependencies

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

---

### Step 2 — Environment config

Create a `.env` file in the project root:

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

---

### Step 3 — Database connection helpers

**`app/db/connection.py`** — reusable functions for running SQL queries:

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

---

### Step 4 — First endpoints and server

Create two simple endpoints to verify the API and database are working.

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

### Step 5 — Create the `players` table and seed it

Write `scripts/seed.py` to create the database schema and seed it with pre-made players so that we can test the multiplayer feature later on:

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
	('Player1', 'pass1'),
	('Player2', 'pass2'),
    ('Player3', 'pass3'),
    ('Player4', 'pass4');
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
- `VARCHAR(50) UNIQUE NOT NULL` — usernames must be unique and can't be empty. 50 chars is generous but prevents abuse.
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

---

### Step 6 — Install auth dependencies

Install the two libraries needed for authentication:

```bash
pip install bcrypt "python-jose[cryptography]"
```

| Package                     | Why                                                                                                                                         |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `bcrypt`                    | Password hashing. bcrypt is deliberately slow, which makes brute-force attacks impractical. We use it directly — no wrapper library needed. |
| `python-jose[cryptography]` | Creates and verifies JSON Web Tokens (JWTs). The `[cryptography]` extra gives it a fast C backend for signing operations.                   |

**Why two separate libraries?** They solve different problems:

- `bcrypt` turns a plain password into an irreversible hash for storage. You can verify a password against a hash, but you can never recover the original password from the hash.
- `python-jose` creates a signed token containing data (like a player ID). The token is not encrypted — anyone can read its contents — but only the server can create valid ones because only the server knows the `SECRET_KEY`.

---

### Step 7 — Update settings for auth

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

### Step 8 — Add a write helper

So far, `db/connection.py` only has `fetch_one()` and `fetch_all()` — both are read-only. They work for SELECT queries, but when you INSERT, UPDATE, or DELETE, two things are different:

1. **You need to commit.** PostgreSQL runs inside a transaction. Reads work without committing, but writes must be explicitly committed or they're rolled back when the connection closes. Your changes would simply vanish.
2. **You often want the result back.** After inserting a new player, you want to know the `id` PostgreSQL assigned. SQL's `RETURNING` clause does this: `INSERT INTO players (...) VALUES (...) RETURNING id;`.

Add this function to **`app/db/connection.py`**:

```python
def execute(sql: str, params: tuple | None = None) -> dict | None:
    """Execute a write query (INSERT/UPDATE/DELETE) and return the result."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.fetchone()
```

The full file should now look like this:

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


def execute(sql: str, params: tuple | None = None) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.fetchone()
```

**Why doesn't `fetch_one` / `fetch_all` need `conn.commit()`?**

SELECT queries don't modify data, so there's nothing to commit. psycopg opens a transaction automatically, and when the `with` block ends, the connection closes and the transaction is discarded — which is fine because nothing changed.

With `execute()`, we're changing data. If we don't call `conn.commit()` before the `with` block ends, psycopg rolls back the transaction and the INSERT/UPDATE/DELETE has no effect.

**Usage example** (you'll use this pattern in the register endpoint later):

```python
player = execute(
    "INSERT INTO players (username, password_hash) VALUES (%s, %s) RETURNING id;",
    ("alice", "$2b$12$...")
)
# player = {"id": 1}
```

The `RETURNING id` clause tells PostgreSQL to send back the auto-generated ID, which `cur.fetchone()` captures as a dictionary.

---

### Step 9 — Create `core/security.py`

This file is responsible for one thing: turning passwords into hashes and verifying them. We use `bcrypt` directly — no wrapper library needed.

Create **`app/core/security.py`**:

```python
import bcrypt


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
```

**How it works:**

`bcrypt.gensalt()` generates a random salt. `bcrypt.hashpw()` hashes the password with that salt. Both functions work with bytes, so we `.encode()` the string input and `.decode()` the bytes output.

**`hash_password("secret123")`** produces something like:

```
$2b$12$LJ3m4ys7Gk2nR1Kx8qVZz.abc123...
```

Breaking this down:

- `$2b$` — bcrypt algorithm identifier
- `12$` — cost factor (2^12 = 4096 iterations). Higher = slower = harder to brute-force
- The rest — the salt (random, auto-generated) and the hash, combined into one string

**`verify_password("secret123", "$2b$12$LJ3m...")`** hashes `"secret123"` with the same salt embedded in the stored hash and checks if they match. Returns `True` or `False`.

You never compare passwords directly. You never decrypt a hash. You only check: "does this plaintext, when hashed, produce the same result?"

---

### Step 10 — Create `core/auth.py`

This file handles two things:

1. **Creating** JWT tokens (after login/register)
2. **Validating** JWT tokens (on every protected request)

Create **`app/core/auth.py`**:

```python
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.core.settings import settings
from app.db.connection import fetch_one

security_scheme = HTTPBearer()


def create_access_token(player_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(player_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_current_player(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        player_id = payload.get("sub")
        if player_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    player = fetch_one(
        "SELECT id, username, created_at FROM players WHERE id = %s;",
        (int(player_id),),
    )
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Player not found",
        )
    return player
```

**`create_access_token(player_id)`** — builds the JWT:

- `payload` is a dictionary with two standard JWT claims:
  - `"sub"` (subject) — identifies who the token is about. We store the player ID as a string (JWT convention).
  - `"exp"` (expiration) — timestamp after which the token is invalid. `python-jose` checks this automatically on decode.
- `jwt.encode()` signs the payload with your `SECRET_KEY` using HS256. The output is a string like `eyJhbGciOi...` — three base64 segments separated by dots (header.payload.signature).

**`get_current_player(credentials)`** — this is a **FastAPI dependency**. Here's the flow:

1. **`HTTPBearer()`** — tells FastAPI to look for an `Authorization: Bearer <token>` header. In `/docs`, this adds a 🔒 button where you can paste your token.
2. **`Depends(security_scheme)`** — FastAPI calls `HTTPBearer()` automatically before your function runs. It extracts the token from the header and passes it as `credentials`.
3. **`jwt.decode()`** — verifies the signature and checks expiration. If the token was tampered with or expired, it raises `JWTError`.
4. **Database lookup** — we fetch the actual player from the DB. This ensures the token belongs to a real, existing player (not a deleted account).
5. **Return value** — the player dict is passed to any route that uses `Depends(get_current_player)`.

If anything fails at any step → 401 Unauthorized.

**Why not just trust the token without a DB lookup?** You could — the token is signed, so you know it's authentic. But if a player is deleted after the token was issued, the token would still work. The DB check prevents this.

---

### Step 11 — Create `routers/auth.py`

This is where the register and login endpoints live. They use the helpers from the previous two steps.

Create **`app/routers/auth.py`**:

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.db.connection import fetch_one, execute
from app.core.security import hash_password, verify_password
from app.core.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new player",
)
def register(body: AuthRequest):
    existing = fetch_one(
        "SELECT id FROM players WHERE username = %s;", (body.username,)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    hashed = hash_password(body.password)
    player = execute(
        "INSERT INTO players (username, password_hash) VALUES (%s, %s) RETURNING id;",
        (body.username, hashed),
    )
    token = create_access_token(player["id"])
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get an access token",
)
def login(body: AuthRequest):
    player = fetch_one(
        "SELECT id, password_hash FROM players WHERE username = %s;",
        (body.username,),
    )
    if not player or not verify_password(body.password, player["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(player["id"])
    return TokenResponse(access_token=token)
```

**Pydantic models** — FastAPI uses these to validate request bodies and shape responses:

- `AuthRequest` — both register and login accept the same shape: `{"username": "...", "password": "..."}`. If a field is missing or the wrong type, FastAPI returns a 422 error automatically. You don't write any validation code.
- `TokenResponse` — defines what the response looks like. `response_model=TokenResponse` tells FastAPI to strip any extra fields and show this shape in `/docs`. The `token_type` has a default of `"bearer"` — this is an OAuth2 convention that tells the client how to use the token (put it in the `Authorization: Bearer <token>` header).

**Register flow:**

1. Check if the username is taken → 409 Conflict if so
2. Hash the password (never store plain text)
3. INSERT into the database, get the new `id` back via `RETURNING`
4. Create a JWT with that `id`
5. Return the token — the user is logged in immediately after registering

**Login flow:**

1. Look up the player by username
2. Verify the password hash — `verify_password()` returns `True`/`False`
3. If either step fails → 401. The error message is deliberately vague ("Invalid username or password") so attackers can't tell whether the username exists
4. Create and return a JWT

**Why one `AuthRequest` model instead of separate `RegisterRequest`/`LoginRequest`?** They have identical fields. If register later needs extra fields (e.g., email), you'd split them then. Until that happens, keep it simple.

### Step 12 — Create `routers/players.py`

This router has a single protected endpoint that returns the authenticated player's profile. It's the simplest way to verify the entire auth chain is working end-to-end.

Create **`app/routers/players.py`**:

```python
from fastapi import APIRouter, Depends
from app.core.auth import get_current_player

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/me", summary="Get my profile")
def get_me(player: dict = Depends(get_current_player)):
    return player
```

That's the entire file. Here's what happens when a request hits `GET /players/me`:

1. FastAPI sees `Depends(get_current_player)` in the function signature
2. It calls `get_current_player()` **before** your function runs
3. `get_current_player()` extracts the Bearer token from the header, decodes the JWT, looks up the player in the database
4. If everything succeeds, the player dict is passed as the `player` parameter
5. If anything fails (no token, expired token, invalid token, deleted player), a 401 response is returned — your function never executes

**`Depends()` is FastAPI's dependency injection.** It's the framework's way of saying "run this other function first, and give me the result." You'll use the same pattern across all protected endpoints — just add `player: dict = Depends(get_current_player)` to any route that requires authentication.

The response will look like:

```json
{
	"id": 1,
	"username": "alice",
	"created_at": "2026-03-30T12:00:00"
}
```

Note: `password_hash` is **not** in the response because the SQL query in `get_current_player()` only selects `id, username, created_at`. This is intentional — never return sensitive data that the client doesn't need.

---

### Step 13 — Update `main.py`

Now wire the new routers into the app and add CORS middleware so the frontend can talk to the API.

Update **`app/main.py`**:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.health import router as health_router
from .routers.db_check import router as db_check_router
from .routers.auth import router as auth_router
from .routers.players import router as players_router

app = FastAPI(title="Connect4 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"], summary="Root endpoint")
def root() -> dict:
    return {"status": "ok", "message": "API is running!"}


app.include_router(health_router)
app.include_router(db_check_router)
app.include_router(auth_router)
app.include_router(players_router)
```

**What changed:**

- **Added `auth_router`** — exposes `POST /auth/register` and `POST /auth/login`
- **Updated `players_router`** — now points to the new `players.py` with the protected `/players/me` endpoint
- **Added CORS middleware** — this is essential for frontend ↔ backend communication

**Why CORS?**

When your frontend (served from `localhost:3000` or a file) makes a `fetch()` request to the API (on `localhost:8000`), the browser blocks it by default — they're different **origins** (different port = different origin). This is a security feature called the Same-Origin Policy.

CORS (Cross-Origin Resource Sharing) tells the browser: "it's OK, I trust requests from these origins." The middleware adds the necessary response headers.

`allow_origins=["*"]` means "allow any origin." This is fine for development. In production, you'd restrict it to your actual frontend domain:

```python
allow_origins=["https://yourgame.com"]
```

**Test the full auth flow in `/docs`:**

1. Start the server: `uvicorn app.main:app --reload`
2. Open http://127.0.0.1:8000/docs
3. **POST /auth/register** — send `{"username": "alice", "password": "secret123"}` → you get a token
4. Click the 🔒 **Authorize** button (top right of the page)
5. Paste the token string (just the token, not "Bearer ...")
6. **GET /players/me** → should return alice's profile
7. Try without a token → 401
8. **POST /auth/login** — same credentials → fresh token
9. Try a wrong password → 401 "Invalid username or password"
10. Try registering "alice" again → 409 "Username already taken"

---

### Step 14 — Create `ws/manager.py` — the lobby + room tracker

All lobby and game state lives **in memory** — no database tables needed. When the server restarts, lobbies and in-progress games are lost, which is fine for a real-time game. The `ConnectionManager` is responsible for:

- Tracking open lobbies (games waiting for a second player)
- Tracking active games (two connected players)
- Relaying messages between both players in a game

Create the folder and files:

```
app/
└── ws/
    ├── __init__.py
    └── manager.py
```

**`app/ws/manager.py`**:

```python
from fastapi import WebSocket


class Game:
    """Represents a single game room (lobby or in-progress)."""

    def __init__(self, game_id: str, host: dict, ws: WebSocket):
        self.game_id = game_id
        self.host = host            # player dict from get_current_player
        self.guest = None           # filled when someone joins
        self.connections: dict[int, WebSocket] = {host["id"]: ws}

    @property
    def is_full(self) -> bool:
        return self.guest is not None

    def add_guest(self, player: dict, ws: WebSocket):
        self.guest = player
        self.connections[player["id"]] = ws

    async def broadcast(self, message: dict):
        """Send a JSON message to all connected players."""
        for ws in self.connections.values():
            await ws.send_json(message)

    async def send_to(self, player_id: int, message: dict):
        """Send a JSON message to a specific player."""
        ws = self.connections.get(player_id)
        if ws:
            await ws.send_json(message)

    def other_id(self, player_id: int) -> int | None:
        """Return the other player's ID, or None if solo."""
        if player_id == self.host["id"] and self.guest:
            return self.guest["id"]
        if self.guest and player_id == self.guest["id"]:
            return self.host["id"]
        return None


class ConnectionManager:
    """Tracks all lobbies and active games in memory."""

    def __init__(self):
        self.games: dict[str, Game] = {}  # game_id -> Game

    def create_game(self, game_id: str, host: dict, ws: WebSocket) -> Game:
        game = Game(game_id, host, ws)
        self.games[game_id] = game
        return game

    def get_game(self, game_id: str) -> Game | None:
        return self.games.get(game_id)

    def remove_game(self, game_id: str):
        self.games.pop(game_id, None)

    def get_open_lobbies(self) -> list[dict]:
        """Return all games that are waiting for a second player."""
        return [
            {"game_id": g.game_id, "host": g.host["username"]}
            for g in self.games.values()
            if not g.is_full
        ]


manager = ConnectionManager()
```

**Key design decisions:**

- **No board, no turns, no win detection on the server.** The server is a relay — it forwards moves between the two clients. All game logic (coin drops, win checks, turn tracking) stays in the frontend, which already implements it.
- **`Game.connections`** — maps `player_id → WebSocket`. This lets us relay a move from one player to the other, or broadcast messages to both.
- **`Game.other_id()`** — helper to find the opponent's ID so we can forward moves to the right player.
- **`manager` singleton** — one global instance shared across all WebSocket connections. Since Uvicorn runs in a single process (with `--reload`), all connections share the same Python objects in memory.
- **No database** — lobbies and games are ephemeral. They exist only while players are connected. Server restart = clean slate.

---

### Step 15 — Create `routers/lobbies.py` — REST endpoints for lobby listing

Clients need a way to discover open lobbies **before** connecting via WebSocket. This is a simple REST endpoint — no WebSocket involved yet.

Create **`app/routers/lobbies.py`**:

```python
from fastapi import APIRouter
from app.ws.manager import manager

router = APIRouter(prefix="/lobbies", tags=["lobbies"])


@router.get("", summary="List open lobbies")
def list_lobbies():
    return manager.get_open_lobbies()
```

The response is a list of lobbies waiting for a second player:

```json
[{ "game_id": "abc123", "host": "alice" }]
```

The frontend will poll this endpoint (or fetch it once when entering the online menu) to show available games. Once a player picks a lobby, the frontend connects via WebSocket (next step).

**Why REST instead of WebSocket for listing?** Listing lobbies is a one-shot read — the client asks, gets a list, renders it. WebSocket is overkill for that. The WebSocket connection starts when the player actually creates or joins a game.

---

### Step 16 — Create `ws/game.py` — the WebSocket endpoint

This is the core of multiplayer — the WebSocket endpoint where players connect to create or join games. The server doesn't track the board or enforce rules — it's a **relay** that forwards each player's actions to their opponent. All game logic (coin drops, turn tracking, win detection) stays in the frontend.

Create **`app/ws/game.py`**:

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from app.core.settings import settings
from app.db.connection import fetch_one
from app.ws.manager import manager

router = APIRouter()


def authenticate_ws(token: str) -> dict | None:
    """Validate a JWT token and return the player dict, or None."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        player_id = payload.get("sub")
        if player_id is None:
            return None
    except JWTError:
        return None

    return fetch_one(
        "SELECT id, username FROM players WHERE id = %s;",
        (int(player_id),),
    )


@router.websocket("/ws/games/{game_id}")
async def game_ws(ws: WebSocket, game_id: str, token: str = Query(...)):
    # --- Auth ---
    player = authenticate_ws(token)
    if not player:
        await ws.close(code=4001, reason="Invalid or expired token")
        return

    await ws.accept()

    # --- Join or create ---
    game = manager.get_game(game_id)

    if game is None:
        # No game with this ID exists → create a new lobby
        game = manager.create_game(game_id, player, ws)
        await ws.send_json({
            "type": "waiting",
            "message": "Lobby created. Waiting for opponent...",
            "game_id": game_id,
            "color": "Yellow",
        })

    elif not game.is_full:
        # Lobby exists and needs a second player → join
        if player["id"] == game.host["id"]:
            await ws.send_json({"type": "error", "message": "You are already the host"})
            await ws.close()
            return

        game.add_guest(player, ws)
        await game.broadcast({
            "type": "start",
            "message": "Game started!",
            "game_id": game_id,
            "host": game.host["username"],
            "guest": game.guest["username"],
            "turn": game.host["username"],
        })

    else:
        # Game is full → reject
        await ws.send_json({"type": "error", "message": "Game is full"})
        await ws.close()
        return

    # --- Relay loop ---
    try:
        while True:
            data = await ws.receive_json()

            # Forward the message to the other player
            other = game.other_id(player["id"])
            if other is None:
                await ws.send_json({
                    "type": "error",
                    "message": "Waiting for opponent",
                })
                continue

            # Attach the sender's info and relay
            data["player"] = player["username"]
            await game.send_to(other, data)

    except WebSocketDisconnect:
        # Notify the other player and clean up
        game.connections.pop(player["id"], None)
        if game.connections:
            for remaining_ws in game.connections.values():
                await remaining_ws.send_json({
                    "type": "opponent_left",
                    "message": f"{player['username']} disconnected",
                })
        manager.remove_game(game_id)
```

**The WebSocket URL:**

```
ws://localhost:8000/ws/games/{game_id}?token=<JWT>
```

- `game_id` — any string. To **create** a lobby, the host picks a unique ID (we'll use `uuid4` on the frontend). To **join**, the guest uses an existing game's ID from the lobby list.
- `token` — the JWT from login/register. WebSockets don't support `Authorization` headers in browsers, so we pass the token as a query parameter.

**Why `authenticate_ws()` instead of reusing `get_current_player()`?** The `get_current_player()` dependency uses FastAPI's `Depends(HTTPBearer())`, which only works with HTTP requests. WebSocket connections don't have standard HTTP headers in the browser, so we extract the token from the query string and validate it manually. Same logic, different plumbing.

**The relay approach — why no game logic on the server?**

The frontend already has full Connect 4 game logic — coin drop animations, win detection via CSS class scanning, turn tracking. Rather than duplicating all of that on the server, the backend acts as a **dumb pipe**: whatever message one client sends gets forwarded to the other, with the sender's username attached. The frontend handles everything else.

This means we're trusting the clients. A malicious player could send fake moves, but for a casual game between friends this is fine. The tradeoff is simplicity — the entire relay loop is ~10 lines of code.

**Message flow:**

1. Player A clicks a column → frontend drops the coin locally → sends `{"type": "move", "column": 3}` to the server
2. Server attaches `"player": "alice"` and forwards it to Player B
3. Player B's frontend receives the message and drops the coin in column 3
4. Player B's frontend detects it's now their turn
5. If either frontend detects a win, it shows the win screen locally

**Message types — server → client (server-generated):**

| `type`          | When                      | Key fields              |
| --------------- | ------------------------- | ----------------------- |
| `waiting`       | Host creates a lobby      | `game_id`, `color`      |
| `start`         | Guest joins, game begins  | `host`, `guest`, `turn` |
| `error`         | Invalid action            | `message`               |
| `opponent_left` | Other player disconnected | `message`               |

**Message types — client → server → other client (relayed):**

Any JSON the client sends is forwarded to the opponent with `"player"` attached. The frontend decides what types to send — the server doesn't inspect or validate them. Typical messages:

| `type` | Fields   | Purpose                              |
| ------ | -------- | ------------------------------------ |
| `move` | `column` | Player dropped a coin in this column |
| `win`  | —        | Player's frontend detected a win     |

**Disconnection handling:** When a player's WebSocket closes (browser tab closed, network drop), `WebSocketDisconnect` fires. The server notifies the remaining player and removes the game entirely. No reconnection support — if you disconnect, the game is over.

---

### Step 17 — Update `main.py` — wire WebSocket + lobbies

Add the new routers to the app:

Update **`app/main.py`**:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.health import router as health_router
from .routers.db_check import router as db_check_router
from .routers.auth import router as auth_router
from .routers.players import router as players_router
from .routers.lobbies import router as lobbies_router
from .ws.game import router as game_ws_router

app = FastAPI(title="Connect4 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"], summary="Root endpoint")
def root() -> dict:
    return {"status": "ok", "message": "API is running!"}


app.include_router(health_router)
app.include_router(db_check_router)
app.include_router(auth_router)
app.include_router(players_router)
app.include_router(lobbies_router)
app.include_router(game_ws_router)
```

Two new lines:

- `lobbies_router` — the `GET /lobbies` REST endpoint from Step 15
- `game_ws_router` — the `ws://host/ws/games/{game_id}` WebSocket endpoint from Step 16

---

### Step 18 — Freeze dependencies

```bash
pip freeze > requirements.txt
```

This locks every package and its exact version so anyone cloning the repo gets the same environment.

---

### Step 19 — Test the full flow

You can test the WebSocket with two browser tabs (or use a WebSocket client like Postman or `websocat`).

**Setup:**

1. Start the server: `uvicorn app.main:app --reload`
2. Register two players via `/docs`:
   - `POST /auth/register` → `{"username": "alice", "password": "secret123"}` → save token A
   - `POST /auth/register` → `{"username": "bob", "password": "secret456"}` → save token B

**Test lobby listing:**

3. `GET /lobbies` → `[]` (no lobbies yet)

**Test game creation (Player A = host):**

4. Connect Player A via WebSocket:
   ```
   ws://localhost:8000/ws/games/test-game-1?token=<token_A>
   ```
5. Player A receives: `{"type": "waiting", "message": "Lobby created...", "game_id": "test-game-1", "color": "Yellow"}`
6. `GET /lobbies` → `[{"game_id": "test-game-1", "host": "alice"}]`

**Test joining (Player B = guest):**

7. Connect Player B to the same game:
   ```
   ws://localhost:8000/ws/games/test-game-1?token=<token_B>
   ```
8. Both players receive: `{"type": "start", "host": "alice", "guest": "bob", "turn": "alice"}`
9. `GET /lobbies` → `[]` (game is full, no longer listed)

**Test gameplay:**

10. Player A sends: `{"type": "move", "column": 3}` → Player B receives `{"type": "move", "column": 3, "player": "alice"}`
11. Player B sends: `{"type": "move", "column": 4}` → Player A receives `{"type": "move", "column": 4, "player": "bob"}`
12. Messages are only forwarded to the **other** player — you don't receive your own messages back

**Test disconnection:**

13. Close Player A's WebSocket → Player B receives `{"type": "opponent_left"}`
14. `GET /lobbies` → `[]` (game was removed)
