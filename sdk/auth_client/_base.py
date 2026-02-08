"""Shared configuration and error-mapping logic for sync and async clients."""

from __future__ import annotations

import httpx

from auth_client.exceptions import (
    AuthenticationError,
    AuthorizationError,
    AuthServiceError,
    NotFoundError,
    ServerError,
    ValidationError,
)
from auth_client.models import (
    ApiKey,
    ApiKeyCreated,
    ApiKeyList,
    AuditLog,
    AuditLogEntry,
    HealthStatus,
    Message,
    PaginationMeta,
    Session,
    TokenPair,
    User,
    UserList,
)

_STATUS_MAP: dict[int, type[AuthServiceError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    422: ValidationError,
}


def raise_for_status(response: httpx.Response) -> None:
    """Map non-2xx responses to typed exceptions."""
    if response.is_success:
        return

    code = response.status_code
    try:
        body = response.json()
        detail = body.get("detail", response.text)
    except Exception:
        detail = response.text

    if code in _STATUS_MAP:
        raise _STATUS_MAP[code](detail, status_code=code, detail=detail)
    if code >= 500:
        raise ServerError(detail, status_code=code, detail=detail)
    raise AuthServiceError(detail, status_code=code, detail=detail)


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------


def _parse_token_pair(data: dict) -> TokenPair:
    return TokenPair(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        token_type=data.get("token_type", "bearer"),
    )


def _parse_message(data: dict) -> Message:
    return Message(message=data["message"])


def _parse_user(data: dict) -> User:
    return User(
        id=data["id"],
        email=data["email"],
        role=data["role"],
        is_active=data["is_active"],
        is_verified=data["is_verified"],
        created_at=str(data["created_at"]),
        updated_at=str(data["updated_at"]),
        display_name=data.get("display_name"),
        phone=data.get("phone"),
        metadata=data.get("metadata"),
    )


def _parse_pagination(data: dict) -> PaginationMeta:
    return PaginationMeta(
        page=data["page"],
        per_page=data["per_page"],
        total=data["total"],
        total_pages=data["total_pages"],
    )


def _parse_user_list(data: dict) -> UserList:
    return UserList(
        data=[_parse_user(u) for u in data["data"]],
        pagination=_parse_pagination(data["pagination"]),
    )


def _parse_session(data: dict) -> Session:
    return Session(
        id=data["id"],
        created_at=str(data["created_at"]),
        user_agent=data.get("user_agent"),
        ip_address=data.get("ip_address"),
    )


def _parse_api_key(data: dict) -> ApiKey:
    return ApiKey(
        id=data["id"],
        name=data["name"],
        key_prefix=data["key_prefix"],
        created_by=data["created_by"],
        usage_count=data.get("usage_count", 0),
        created_at=str(data["created_at"]),
        expires_at=str(data["expires_at"]) if data.get("expires_at") else None,
        revoked_at=str(data["revoked_at"]) if data.get("revoked_at") else None,
        last_used_at=str(data["last_used_at"]) if data.get("last_used_at") else None,
        rate_limit=data.get("rate_limit"),
    )


def _parse_api_key_created(data: dict) -> ApiKeyCreated:
    return ApiKeyCreated(
        id=data["id"],
        name=data["name"],
        key_prefix=data["key_prefix"],
        created_by=data["created_by"],
        usage_count=data.get("usage_count", 0),
        created_at=str(data["created_at"]),
        expires_at=str(data["expires_at"]) if data.get("expires_at") else None,
        revoked_at=str(data["revoked_at"]) if data.get("revoked_at") else None,
        last_used_at=str(data["last_used_at"]) if data.get("last_used_at") else None,
        rate_limit=data.get("rate_limit"),
        key=data["key"],
    )


def _parse_api_key_list(data: dict) -> ApiKeyList:
    return ApiKeyList(data=[_parse_api_key(k) for k in data["data"]])


def _parse_audit_log(data: dict) -> AuditLog:
    entries = [
        AuditLogEntry(
            id=e["id"],
            event=e["event"],
            created_at=str(e["created_at"]),
            user_id=e.get("user_id"),
            ip_address=e.get("ip_address"),
            user_agent=e.get("user_agent"),
            details=e.get("details"),
        )
        for e in data["data"]
    ]
    return AuditLog(
        data=entries,
        pagination=_parse_pagination(data["pagination"]),
    )


def _parse_health(data: dict) -> HealthStatus:
    return HealthStatus(
        status=data["status"],
        timestamp=data["timestamp"],
        database=data["database"],
    )


class BaseClientConfig:
    """Mixin providing URL helpers, header building, and token storage."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self._base_url = base_url.rstrip("/")
        self._access_token: str | None = None

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _auth_headers(self) -> dict[str, str]:
        if not self._access_token:
            return {}
        return {"Authorization": f"Bearer {self._access_token}"}

    def set_token(self, token: str) -> None:
        """Manually set the access token used for authenticated requests."""
        self._access_token = token

    def clear_token(self) -> None:
        """Clear the stored access token."""
        self._access_token = None
