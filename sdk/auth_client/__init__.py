"""Auth Service Python Client SDK."""

from auth_client._async import AsyncAuthClient
from auth_client._sync import AuthClient
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
    HealthStatus,
    Message,
    PaginationMeta,
    Session,
    TokenPair,
    User,
    UserList,
)

__all__ = [
    "AuthClient",
    "AsyncAuthClient",
    "AuthServiceError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "TokenPair",
    "Message",
    "User",
    "UserList",
    "Session",
    "ApiKey",
    "ApiKeyCreated",
    "ApiKeyList",
    "AuditLog",
    "PaginationMeta",
    "HealthStatus",
]
