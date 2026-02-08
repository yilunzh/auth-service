from datetime import datetime

from pydantic import BaseModel


class CreateApiKeyRequest(BaseModel):
    name: str
    expires_at: datetime | None = None
    rate_limit: int | None = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    created_by: str
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None
    usage_count: int = 0
    rate_limit: int | None = None
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyResponse):
    key: str  # Full key shown only on creation


class ApiKeyListResponse(BaseModel):
    data: list[ApiKeyResponse]
