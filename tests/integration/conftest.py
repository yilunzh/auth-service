"""Integration test helper fixtures.

These fixtures use the real DB (via db_conn) and the ASGI test client.
"""

import uuid
from datetime import datetime

import pytest

from app.services.password import hash_password

TEST_PASSWORD = "TestPassword_Xk9m!z"


async def _create_user(conn, email="user@test.com", role="user", is_verified=True, is_active=True):
    """Insert a user directly into the DB and return the user dict."""
    user_id = str(uuid.uuid4())
    pw_hash = await hash_password(TEST_PASSWORD)
    now = datetime.utcnow()

    async with conn.cursor() as cur:
        await cur.execute(
            """INSERT INTO users (id, email, password_hash, role, is_active, is_verified, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, email, pw_hash, role, int(is_active), int(is_verified), now, now),
        )

    return {
        "id": user_id,
        "email": email,
        "role": role,
        "is_active": is_active,
        "is_verified": is_verified,
        "password_hash": pw_hash,
    }


@pytest.fixture
async def test_user(db_conn):
    """Create a verified regular user."""
    return await _create_user(db_conn, email="testuser@test.com")


@pytest.fixture
async def verified_user(db_conn):
    """Alias for test_user with a different email."""
    return await _create_user(db_conn, email="verified@test.com")


@pytest.fixture
async def admin_user(db_conn):
    """Create a verified admin user."""
    return await _create_user(db_conn, email="admin@test.com", role="admin")


async def _login_user(test_client, email, password=TEST_PASSWORD):
    """Helper to log in and return the token response."""
    resp = await test_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()


@pytest.fixture
async def auth_headers(test_client, test_user):
    """Return Authorization headers for a regular user."""
    tokens = await _login_user(test_client, test_user["email"])
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
async def admin_headers(test_client, admin_user):
    """Return Authorization headers for an admin user."""
    tokens = await _login_user(test_client, admin_user["email"])
    return {"Authorization": f"Bearer {tokens['access_token']}"}
