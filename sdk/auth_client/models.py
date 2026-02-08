"""Dataclass response models for the Auth Service API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass
class Message:
    message: str


@dataclass
class User:
    id: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: str
    display_name: str | None = None
    phone: str | None = None
    metadata: dict | None = None


@dataclass
class PaginationMeta:
    page: int
    per_page: int
    total: int
    total_pages: int


@dataclass
class UserList:
    data: list[User]
    pagination: PaginationMeta


@dataclass
class Session:
    id: str
    created_at: str
    user_agent: str | None = None
    ip_address: str | None = None


@dataclass
class ApiKey:
    id: str
    name: str
    key_prefix: str
    created_by: str
    usage_count: int
    created_at: str
    expires_at: str | None = None
    revoked_at: str | None = None
    last_used_at: str | None = None
    rate_limit: int | None = None


@dataclass
class ApiKeyCreated(ApiKey):
    key: str = ""


@dataclass
class ApiKeyList:
    data: list[ApiKey]


@dataclass
class AuditLogEntry:
    id: int
    event: str
    created_at: str
    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    details: dict | None = None


@dataclass
class AuditLog:
    data: list[AuditLogEntry]
    pagination: PaginationMeta


@dataclass
class HealthStatus:
    status: str
    timestamp: str
    database: str
