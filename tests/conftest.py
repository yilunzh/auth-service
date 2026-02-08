"""Root test fixtures.

Environment overrides are set BEFORE any app imports so that the app
configuration module picks up test values.
"""

import os

# ---------------------------------------------------------------------------
# Environment overrides — MUST be set before importing anything from `app`
# ---------------------------------------------------------------------------
os.environ["DATABASE_URL"] = "mysql://root:rootpassword@localhost:3306/auth_db_test"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-not-for-production"
os.environ["ARGON2_TIME_COST"] = "1"
os.environ["ARGON2_MEMORY_COST"] = "1024"
os.environ["ARGON2_PARALLELISM"] = "1"
os.environ["DEBUG"] = "1"
os.environ["SMTP_HOST"] = "localhost"
os.environ["SMTP_PORT"] = "1025"
os.environ["BASE_URL"] = "http://testserver"

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiomysql
import httpx
import pytest

# Now safe to import app modules
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session.

    Required by pytest-asyncio <1.0 (used in CI) so that session-scoped
    async fixtures share one loop.  Newer pytest-asyncio (>=1.0) uses the
    asyncio_default_*_loop_scope config options in pyproject.toml instead,
    but silently tolerates this fixture.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    """Session-scoped fixture: create test DB and connection pool.

    Connects as root, creates auth_db_test, runs the schema migration,
    then creates a pool and patches the app's global pool.
    """
    # Connect as root to create the test database
    root_conn = await aiomysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="rootpassword",
        autocommit=True,
        charset="utf8mb4",
    )

    async with root_conn.cursor() as cur:
        await cur.execute("CREATE DATABASE IF NOT EXISTS auth_db_test")
        await cur.execute("USE auth_db_test")

        # Run the migration script
        migration_path = (
            Path(__file__).parent.parent / "app" / "db" / "migrations" / "001_initial.sql"
        )
        sql = migration_path.read_text()
        # Execute each statement separately
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                await cur.execute(statement)

    root_conn.close()

    # Create a pool for the test database
    pool = await aiomysql.create_pool(
        host="localhost",
        port=3306,
        user="root",
        password="rootpassword",
        db="auth_db_test",
        minsize=2,
        maxsize=10,
        autocommit=True,
        charset="utf8mb4",
    )

    # Patch the app's global pool
    import app.db.pool as pool_module

    original_pool = pool_module._pool
    pool_module._pool = pool

    yield pool

    # Restore and clean up
    pool_module._pool = original_pool
    pool.close()
    await pool.wait_closed()


# Tables in FK-safe truncation order
_ALL_TABLES = [
    "audit_log",
    "rate_limits",
    "password_reset_tokens",
    "email_verification_tokens",
    "refresh_tokens",
    "api_keys",
    "users",
]


@pytest.fixture
async def db_conn(db_pool):
    """Function-scoped fixture: yields a connection and truncates all tables after use."""
    async with db_pool.acquire() as conn:
        yield conn

        # Clean up all tables after each test
        async with conn.cursor() as cur:
            await cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in _ALL_TABLES:
                await cur.execute(f"TRUNCATE TABLE {table}")
            await cur.execute("SET FOREIGN_KEY_CHECKS = 1")


@pytest.fixture
async def test_client(db_pool):
    """Async HTTP test client backed by the FastAPI ASGI app.

    Patches send_email to prevent real SMTP calls.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        with patch("app.services.email.send_email", new_callable=AsyncMock):
            yield client
