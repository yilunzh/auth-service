"""Typed exception hierarchy for Auth Service API errors."""

from __future__ import annotations


class AuthServiceError(Exception):
    """Base exception for all Auth Service errors."""

    def __init__(self, message: str, status_code: int, detail: str | None = None):
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(message)


class ValidationError(AuthServiceError):
    """Raised on 400 or 422 responses (bad request / validation failure)."""


class AuthenticationError(AuthServiceError):
    """Raised on 401 responses (invalid or missing credentials)."""


class AuthorizationError(AuthServiceError):
    """Raised on 403 responses (insufficient permissions)."""


class NotFoundError(AuthServiceError):
    """Raised on 404 responses (resource not found)."""


class ServerError(AuthServiceError):
    """Raised on 5xx responses (server-side failure)."""
