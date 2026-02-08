"""Tests for the asynchronous AsyncAuthClient using respx mocks."""

import httpx
import pytest
import respx

from auth_client import (
    AsyncAuthClient,
    AuthenticationError,
    ServerError,
)

BASE = "http://localhost:8000"


@pytest.fixture
async def client():
    async with AsyncAuthClient(BASE) as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@respx.mock
async def test_health(client: AsyncAuthClient):
    respx.get(f"{BASE}/health").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "healthy",
                "timestamp": "2025-01-01T00:00:00+00:00",
                "database": "connected",
            },
        )
    )
    result = await client.health()
    assert result.status == "healthy"


# ---------------------------------------------------------------------------
# Registration & Login
# ---------------------------------------------------------------------------


@respx.mock
async def test_register(client: AsyncAuthClient):
    respx.post(f"{BASE}/api/auth/register").mock(
        return_value=httpx.Response(
            201, json={"message": "Check your email to verify your account"}
        )
    )
    result = await client.register("user@example.com", "password123")
    assert "verify" in result.message.lower()


@respx.mock
async def test_login_stores_token(client: AsyncAuthClient):
    respx.post(f"{BASE}/api/auth/login").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "abc123",
                "refresh_token": "def456",
                "token_type": "bearer",
            },
        )
    )
    tokens = await client.login("user@example.com", "password123")
    assert tokens.access_token == "abc123"
    assert client._access_token == "abc123"


@respx.mock
async def test_refresh_stores_token(client: AsyncAuthClient):
    respx.post(f"{BASE}/api/auth/refresh").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "new_access",
                "refresh_token": "new_refresh",
                "token_type": "bearer",
            },
        )
    )
    tokens = await client.refresh("old_refresh")
    assert tokens.access_token == "new_access"
    assert client._access_token == "new_access"


# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------

_USER_JSON = {
    "id": "u1",
    "email": "user@example.com",
    "role": "user",
    "is_active": True,
    "is_verified": True,
    "display_name": None,
    "phone": None,
    "metadata": None,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
}


@respx.mock
async def test_get_me(client: AsyncAuthClient):
    client.set_token("tok")
    route = respx.get(f"{BASE}/api/auth/me").mock(return_value=httpx.Response(200, json=_USER_JSON))
    user = await client.get_me()
    assert user.id == "u1"
    assert route.calls[0].request.headers["authorization"] == "Bearer tok"


@respx.mock
async def test_update_me(client: AsyncAuthClient):
    client.set_token("tok")
    updated = {**_USER_JSON, "display_name": "Async User"}
    respx.put(f"{BASE}/api/auth/me").mock(return_value=httpx.Response(200, json=updated))
    user = await client.update_me(display_name="Async User")
    assert user.display_name == "Async User"


@respx.mock
async def test_logout(client: AsyncAuthClient):
    client.set_token("tok")
    respx.post(f"{BASE}/api/auth/logout").mock(
        return_value=httpx.Response(200, json={"message": "Logged out successfully."})
    )
    result = await client.logout("refresh_tok")
    assert "logged out" in result.message.lower()


@respx.mock
async def test_list_sessions(client: AsyncAuthClient):
    client.set_token("tok")
    respx.get(f"{BASE}/api/auth/sessions").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "s1",
                    "created_at": "2025-01-01T00:00:00",
                    "user_agent": None,
                    "ip_address": None,
                },
            ],
        )
    )
    sessions = await client.list_sessions()
    assert len(sessions) == 1


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@respx.mock
async def test_list_users(client: AsyncAuthClient):
    client.set_token("admin_tok")
    respx.get(f"{BASE}/api/auth/users").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [_USER_JSON],
                "pagination": {"page": 1, "per_page": 20, "total": 1, "total_pages": 1},
            },
        )
    )
    result = await client.list_users()
    assert len(result.data) == 1


@respx.mock
async def test_get_audit_log(client: AsyncAuthClient):
    client.set_token("admin_tok")
    respx.get(f"{BASE}/api/admin/audit-log").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": 1,
                        "user_id": "u1",
                        "event": "login",
                        "ip_address": None,
                        "user_agent": None,
                        "details": None,
                        "created_at": "2025-01-01T00:00:00",
                    },
                ],
                "pagination": {"page": 1, "per_page": 20, "total": 1, "total_pages": 1},
            },
        )
    )
    result = await client.get_audit_log()
    assert len(result.data) == 1


# ---------------------------------------------------------------------------
# API Key endpoints
# ---------------------------------------------------------------------------

_KEY_JSON = {
    "id": "k1",
    "name": "test-key",
    "key_prefix": "ak_test",
    "created_by": "u1",
    "usage_count": 0,
    "created_at": "2025-01-01T00:00:00",
    "expires_at": None,
    "revoked_at": None,
    "last_used_at": None,
    "rate_limit": None,
}


@respx.mock
async def test_create_api_key(client: AsyncAuthClient):
    client.set_token("admin_tok")
    respx.post(f"{BASE}/api/keys/").mock(
        return_value=httpx.Response(201, json={**_KEY_JSON, "key": "ak_test_secret"})
    )
    result = await client.create_api_key("test-key")
    assert result.key == "ak_test_secret"


@respx.mock
async def test_list_api_keys(client: AsyncAuthClient):
    client.set_token("admin_tok")
    respx.get(f"{BASE}/api/keys/").mock(
        return_value=httpx.Response(200, json={"data": [_KEY_JSON]})
    )
    result = await client.list_api_keys()
    assert len(result.data) == 1


@respx.mock
async def test_revoke_api_key(client: AsyncAuthClient):
    client.set_token("admin_tok")
    respx.delete(f"{BASE}/api/keys/k1").mock(
        return_value=httpx.Response(200, json={"message": "API key revoked."})
    )
    result = await client.revoke_api_key("k1")
    assert "revoked" in result.message.lower()


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------


@respx.mock
async def test_401_raises_authentication_error(client: AsyncAuthClient):
    respx.post(f"{BASE}/api/auth/login").mock(
        return_value=httpx.Response(401, json={"detail": "Invalid credentials"})
    )
    with pytest.raises(AuthenticationError):
        await client.login("bad@example.com", "wrong")


@respx.mock
async def test_500_raises_server_error(client: AsyncAuthClient):
    respx.get(f"{BASE}/health").mock(return_value=httpx.Response(500, json={"detail": "boom"}))
    with pytest.raises(ServerError):
        await client.health()


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------


async def test_set_and_clear_token():
    async with AsyncAuthClient(BASE) as client:
        assert client._access_token is None
        client.set_token("my_token")
        assert client._access_token == "my_token"
        client.clear_token()
        assert client._access_token is None
