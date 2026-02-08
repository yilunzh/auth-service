from datetime import datetime

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    display_name: str | None = None
    phone: str | None = None
    metadata: dict | None = None
    created_at: datetime
    updated_at: datetime


class UpdateProfileRequest(BaseModel):
    display_name: str | None = None
    phone: str | None = None
    metadata: dict | None = None


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class UserListResponse(BaseModel):
    data: list[UserResponse]
    pagination: PaginationMeta


class ChangeRoleRequest(BaseModel):
    role: str = Field(pattern="^(user|admin)$")


class ChangeActiveRequest(BaseModel):
    is_active: bool


class SessionResponse(BaseModel):
    id: str
    created_at: datetime
    user_agent: str | None = None
    ip_address: str | None = None
