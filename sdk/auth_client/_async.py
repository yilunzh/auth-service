"""Asynchronous Auth Service client built on httpx."""

from __future__ import annotations

from datetime import datetime

import httpx

from auth_client._base import (
    BaseClientConfig,
    _parse_api_key,
    _parse_api_key_created,
    _parse_api_key_list,
    _parse_audit_log,
    _parse_health,
    _parse_message,
    _parse_session,
    _parse_token_pair,
    _parse_user,
    _parse_user_list,
    raise_for_status,
)
from auth_client.models import (
    ApiKey,
    ApiKeyCreated,
    ApiKeyList,
    AuditLog,
    HealthStatus,
    Message,
    Session,
    TokenPair,
    User,
    UserList,
)


class AsyncAuthClient(BaseClientConfig):
    """Asynchronous client for the Auth Service API.

    Usage::

        async with AsyncAuthClient("http://localhost:8000") as client:
            tokens = await client.login("user@example.com", "password123")
            me = await client.get_me()
    """

    def __init__(self, base_url: str = "http://localhost:8000", **httpx_kwargs):
        super().__init__(base_url)
        self._client = httpx.AsyncClient(**httpx_kwargs)

    # -- context manager ------------------------------------------------

    async def __aenter__(self) -> AsyncAuthClient:
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    # -- helpers --------------------------------------------------------

    async def _get(self, path: str, *, params: dict | None = None) -> httpx.Response:
        resp = await self._client.get(self._url(path), headers=self._auth_headers(), params=params)
        raise_for_status(resp)
        return resp

    async def _post(self, path: str, *, json: dict | None = None) -> httpx.Response:
        resp = await self._client.post(self._url(path), headers=self._auth_headers(), json=json)
        raise_for_status(resp)
        return resp

    async def _put(self, path: str, *, json: dict | None = None) -> httpx.Response:
        resp = await self._client.put(self._url(path), headers=self._auth_headers(), json=json)
        raise_for_status(resp)
        return resp

    async def _delete(self, path: str) -> httpx.Response:
        resp = await self._client.delete(self._url(path), headers=self._auth_headers())
        raise_for_status(resp)
        return resp

    # ===================================================================
    # Public endpoints
    # ===================================================================

    async def register(self, email: str, password: str) -> Message:
        resp = await self._post("/api/auth/register", json={"email": email, "password": password})
        return _parse_message(resp.json())

    async def login(self, email: str, password: str) -> TokenPair:
        """Authenticate and auto-store the access token on this client."""
        resp = await self._post("/api/auth/login", json={"email": email, "password": password})
        tokens = _parse_token_pair(resp.json())
        self._access_token = tokens.access_token
        return tokens

    async def refresh(self, refresh_token: str) -> TokenPair:
        """Exchange a refresh token for a new pair. Auto-stores the new access token."""
        resp = await self._post("/api/auth/refresh", json={"refresh_token": refresh_token})
        tokens = _parse_token_pair(resp.json())
        self._access_token = tokens.access_token
        return tokens

    async def forgot_password(self, email: str) -> Message:
        resp = await self._post("/api/auth/forgot-password", json={"email": email})
        return _parse_message(resp.json())

    async def reset_password(self, token: str, new_password: str) -> Message:
        resp = await self._post(
            "/api/auth/reset-password", json={"token": token, "new_password": new_password}
        )
        return _parse_message(resp.json())

    async def verify_email(self, token: str) -> Message:
        resp = await self._post("/api/auth/verify-email", json={"token": token})
        return _parse_message(resp.json())

    # ===================================================================
    # Authenticated endpoints
    # ===================================================================

    async def get_me(self) -> User:
        resp = await self._get("/api/auth/me")
        return _parse_user(resp.json())

    async def update_me(
        self,
        *,
        display_name: str | None = None,
        phone: str | None = None,
        metadata: dict | None = None,
    ) -> User:
        body: dict = {}
        if display_name is not None:
            body["display_name"] = display_name
        if phone is not None:
            body["phone"] = phone
        if metadata is not None:
            body["metadata"] = metadata
        resp = await self._put("/api/auth/me", json=body)
        return _parse_user(resp.json())

    async def change_password(self, old_password: str, new_password: str) -> Message:
        resp = await self._put(
            "/api/auth/password",
            json={"old_password": old_password, "new_password": new_password},
        )
        return _parse_message(resp.json())

    async def delete_me(self) -> Message:
        resp = await self._delete("/api/auth/me")
        return _parse_message(resp.json())

    async def logout(self, refresh_token: str) -> Message:
        resp = await self._post("/api/auth/logout", json={"refresh_token": refresh_token})
        return _parse_message(resp.json())

    async def logout_all(self) -> Message:
        resp = await self._post("/api/auth/logout-all")
        return _parse_message(resp.json())

    async def list_sessions(self) -> list[Session]:
        resp = await self._get("/api/auth/sessions")
        return [_parse_session(s) for s in resp.json()]

    # ===================================================================
    # Admin endpoints
    # ===================================================================

    async def list_users(self, *, page: int = 1, per_page: int = 20) -> UserList:
        resp = await self._get("/api/auth/users", params={"page": page, "per_page": per_page})
        return _parse_user_list(resp.json())

    async def change_user_role(self, user_id: str, role: str) -> User:
        resp = await self._put(f"/api/auth/users/{user_id}/role", json={"role": role})
        return _parse_user(resp.json())

    async def change_user_active(self, user_id: str, is_active: bool) -> User:
        resp = await self._put(f"/api/auth/users/{user_id}/active", json={"is_active": is_active})
        return _parse_user(resp.json())

    async def get_audit_log(
        self,
        *,
        user_id: str | None = None,
        event: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> AuditLog:
        params: dict = {"page": page, "per_page": per_page}
        if user_id is not None:
            params["user_id"] = user_id
        if event is not None:
            params["event"] = event
        if start_date is not None:
            params["start_date"] = start_date.isoformat()
        if end_date is not None:
            params["end_date"] = end_date.isoformat()
        resp = await self._get("/api/admin/audit-log", params=params)
        return _parse_audit_log(resp.json())

    # ===================================================================
    # API Key endpoints
    # ===================================================================

    async def create_api_key(
        self,
        name: str,
        *,
        expires_at: datetime | None = None,
        rate_limit: int | None = None,
    ) -> ApiKeyCreated:
        body: dict = {"name": name}
        if expires_at is not None:
            body["expires_at"] = expires_at.isoformat()
        if rate_limit is not None:
            body["rate_limit"] = rate_limit
        resp = await self._post("/api/keys/", json=body)
        return _parse_api_key_created(resp.json())

    async def list_api_keys(self) -> ApiKeyList:
        resp = await self._get("/api/keys/")
        return _parse_api_key_list(resp.json())

    async def get_api_key(self, key_id: str) -> ApiKey:
        resp = await self._get(f"/api/keys/{key_id}")
        return _parse_api_key(resp.json())

    async def rotate_api_key(self, key_id: str, *, grace_hours: int = 24) -> ApiKeyCreated:
        resp = await self._client.post(
            self._url(f"/api/keys/{key_id}/rotate"),
            headers=self._auth_headers(),
            params={"grace_hours": grace_hours},
        )
        raise_for_status(resp)
        return _parse_api_key_created(resp.json())

    async def revoke_api_key(self, key_id: str) -> Message:
        resp = await self._delete(f"/api/keys/{key_id}")
        return _parse_message(resp.json())

    # ===================================================================
    # Health
    # ===================================================================

    async def health(self) -> HealthStatus:
        resp = await self._client.get(self._url("/health"))
        raise_for_status(resp)
        return _parse_health(resp.json())
