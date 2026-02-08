"""Tests for the synchronous AuthClient using respx mocks."""

import httpx
import pytest
import respx

from auth_client import (
    AuthClient,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ServerError,
    ValidationError,
)

BASE = "http://localhost:8000"


@pytest.fixture
def client():
    with AuthClient(BASE) as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@respx.mock
def test_health(client: AuthClient):
    respx.get(f"{BASE}/health").mock(
        return_value=httpx.Response(200, json={
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00+00:00",
            "database": "connected",
        })
    )
    result = client.health()
    assert result.status == "healthy"
    assert result.database == "connected"


# ---------------------------------------------------------------------------
# Registration & Login
# ---------------------------------------------------------------------------


@respx.mock
def test_register(client: AuthClient):
    respx.post(f"{BASE}/api/auth/register").mock(
        return_value=httpx.Response(201, json={"message": "Check your email to verify your account"})
    )
    result = client.register("user@example.com", "password123")
    assert result.message == "Check your email to verify your account"


@respx.mock
def test_login_stores_token(client: AuthClient):
    respx.post(f"{BASE}/api/auth/login").mock(
        return_value=httpx.Response(200, json={
            "access_token": "abc123",
            "refresh_token": "def456",
            "token_type": "bearer",
        })
    )
    tokens = client.login("user@example.com", "password123")
    assert tokens.access_token == "abc123"
    assert tokens.refresh_token == "def456"
    # Token is auto-stored
    assert client._access_token == "abc123"


@respx.mock
def test_refresh_stores_token(client: AuthClient):
    respx.post(f"{BASE}/api/auth/refresh").mock(
        return_value=httpx.Response(200, json={
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "token_type": "bearer",
        })
    )
    tokens = client.refresh("old_refresh")
    assert tokens.access_token == "new_access"
    assert client._access_token == "new_access"


# ---------------------------------------------------------------------------
# Password flows
# ---------------------------------------------------------------------------


@respx.mock
def test_forgot_password(client: AuthClient):
    respx.post(f"{BASE}/api/auth/forgot-password").mock(
        return_value=httpx.Response(200, json={
            "message": "If an account exists with that email, we sent a reset link."
        })
    )
    result = client.forgot_password("user@example.com")
    assert "reset link" in result.message


@respx.mock
def test_reset_password(client: AuthClient):
    respx.post(f"{BASE}/api/auth/reset-password").mock(
        return_value=httpx.Response(200, json={"message": "Password reset successful."})
    )
    result = client.reset_password("tok", "newpass123")
    assert "reset" in result.message.lower()


@respx.mock
def test_verify_email(client: AuthClient):
    respx.post(f"{BASE}/api/auth/verify-email").mock(
        return_value=httpx.Response(200, json={"message": "Email verified successfully."})
    )
    result = client.verify_email("tok")
    assert "verified" in result.message.lower()


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
def test_get_me(client: AuthClient):
    client.set_token("tok")
    route = respx.get(f"{BASE}/api/auth/me").mock(
        return_value=httpx.Response(200, json=_USER_JSON)
    )
    user = client.get_me()
    assert user.id == "u1"
    assert user.email == "user@example.com"
    assert route.calls[0].request.headers["authorization"] == "Bearer tok"


@respx.mock
def test_update_me(client: AuthClient):
    client.set_token("tok")
    updated = {**_USER_JSON, "display_name": "New Name"}
    respx.put(f"{BASE}/api/auth/me").mock(
        return_value=httpx.Response(200, json=updated)
    )
    user = client.update_me(display_name="New Name")
    assert user.display_name == "New Name"


@respx.mock
def test_change_password(client: AuthClient):
    client.set_token("tok")
    respx.put(f"{BASE}/api/auth/password").mock(
        return_value=httpx.Response(200, json={"message": "Password changed successfully."})
    )
    result = client.change_password("old", "newpass123")
    assert "changed" in result.message.lower()


@respx.mock
def test_delete_me(client: AuthClient):
    client.set_token("tok")
    respx.delete(f"{BASE}/api/auth/me").mock(
        return_value=httpx.Response(200, json={"message": "Account deleted successfully."})
    )
    result = client.delete_me()
    assert "deleted" in result.message.lower()


@respx.mock
def test_logout(client: AuthClient):
    client.set_token("tok")
    respx.post(f"{BASE}/api/auth/logout").mock(
        return_value=httpx.Response(200, json={"message": "Logged out successfully."})
    )
    result = client.logout("refresh_tok")
    assert "logged out" in result.message.lower()


@respx.mock
def test_logout_all(client: AuthClient):
    client.set_token("tok")
    respx.post(f"{BASE}/api/auth/logout-all").mock(
        return_value=httpx.Response(200, json={"message": "All sessions revoked."})
    )
    result = client.logout_all()
    assert "revoked" in result.message.lower()


@respx.mock
def test_list_sessions(client: AuthClient):
    client.set_token("tok")
    respx.get(f"{BASE}/api/auth/sessions").mock(
        return_value=httpx.Response(200, json=[
            {"id": "s1", "created_at": "2025-01-01T00:00:00", "user_agent": "curl", "ip_address": "127.0.0.1"},
        ])
    )
    sessions = client.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == "s1"


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@respx.mock
def test_list_users(client: AuthClient):
    client.set_token("admin_tok")
    respx.get(f"{BASE}/api/auth/users").mock(
        return_value=httpx.Response(200, json={
            "data": [_USER_JSON],
            "pagination": {"page": 1, "per_page": 20, "total": 1, "total_pages": 1},
        })
    )
    result = client.list_users()
    assert len(result.data) == 1
    assert result.pagination.total == 1


@respx.mock
def test_change_user_role(client: AuthClient):
    client.set_token("admin_tok")
    respx.put(f"{BASE}/api/auth/users/u1/role").mock(
        return_value=httpx.Response(200, json={**_USER_JSON, "role": "admin"})
    )
    user = client.change_user_role("u1", "admin")
    assert user.role == "admin"


@respx.mock
def test_get_audit_log(client: AuthClient):
    client.set_token("admin_tok")
    respx.get(f"{BASE}/api/admin/audit-log").mock(
        return_value=httpx.Response(200, json={
            "data": [
                {"id": 1, "user_id": "u1", "event": "login", "ip_address": None,
                 "user_agent": None, "details": None, "created_at": "2025-01-01T00:00:00"},
            ],
            "pagination": {"page": 1, "per_page": 20, "total": 1, "total_pages": 1},
        })
    )
    result = client.get_audit_log()
    assert len(result.data) == 1
    assert result.data[0].event == "login"


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
def test_create_api_key(client: AuthClient):
    client.set_token("admin_tok")
    respx.post(f"{BASE}/api/keys/").mock(
        return_value=httpx.Response(201, json={**_KEY_JSON, "key": "ak_test_fullsecret"})
    )
    result = client.create_api_key("test-key")
    assert result.key == "ak_test_fullsecret"
    assert result.name == "test-key"


@respx.mock
def test_list_api_keys(client: AuthClient):
    client.set_token("admin_tok")
    respx.get(f"{BASE}/api/keys/").mock(
        return_value=httpx.Response(200, json={"data": [_KEY_JSON]})
    )
    result = client.list_api_keys()
    assert len(result.data) == 1


@respx.mock
def test_get_api_key(client: AuthClient):
    client.set_token("admin_tok")
    respx.get(f"{BASE}/api/keys/k1").mock(
        return_value=httpx.Response(200, json=_KEY_JSON)
    )
    key = client.get_api_key("k1")
    assert key.id == "k1"


@respx.mock
def test_revoke_api_key(client: AuthClient):
    client.set_token("admin_tok")
    respx.delete(f"{BASE}/api/keys/k1").mock(
        return_value=httpx.Response(200, json={"message": "API key revoked."})
    )
    result = client.revoke_api_key("k1")
    assert "revoked" in result.message.lower()


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------


@respx.mock
def test_401_raises_authentication_error(client: AuthClient):
    respx.post(f"{BASE}/api/auth/login").mock(
        return_value=httpx.Response(401, json={"detail": "Invalid credentials"})
    )
    with pytest.raises(AuthenticationError) as exc_info:
        client.login("bad@example.com", "wrong")
    assert exc_info.value.status_code == 401


@respx.mock
def test_403_raises_authorization_error(client: AuthClient):
    client.set_token("user_tok")
    respx.get(f"{BASE}/api/auth/users").mock(
        return_value=httpx.Response(403, json={"detail": "Admin required"})
    )
    with pytest.raises(AuthorizationError):
        client.list_users()


@respx.mock
def test_404_raises_not_found_error(client: AuthClient):
    client.set_token("admin_tok")
    respx.get(f"{BASE}/api/keys/nonexistent").mock(
        return_value=httpx.Response(404, json={"detail": "API key not found"})
    )
    with pytest.raises(NotFoundError):
        client.get_api_key("nonexistent")


@respx.mock
def test_400_raises_validation_error(client: AuthClient):
    respx.post(f"{BASE}/api/auth/register").mock(
        return_value=httpx.Response(400, json={"detail": "Email already registered"})
    )
    with pytest.raises(ValidationError):
        client.register("dup@example.com", "password123")


@respx.mock
def test_500_raises_server_error(client: AuthClient):
    respx.get(f"{BASE}/health").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"})
    )
    with pytest.raises(ServerError):
        client.health()


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------


def test_set_and_clear_token():
    with AuthClient(BASE) as client:
        assert client._access_token is None
        client.set_token("my_token")
        assert client._access_token == "my_token"
        client.clear_token()
        assert client._access_token is None
