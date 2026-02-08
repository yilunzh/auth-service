from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db import api_keys as db_api_keys
from app.dependencies import get_db, require_admin
from app.models.api_key import (
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ApiKeyResponse,
    CreateApiKeyRequest,
)
from app.models.auth import MessageResponse
from app.services import api_key as api_key_service

router = APIRouter()


@router.post("/", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_api_key(
    body: CreateApiKeyRequest,
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """Create a new API key. The full key is returned only once."""
    try:
        result = await api_key_service.create_key(
            conn,
            name=body.name,
            created_by=admin["id"],
            expires_at=body.expires_at,
            rate_limit=body.rate_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApiKeyCreatedResponse(**result)


@router.get("/", response_model=ApiKeyListResponse)
async def list_api_keys(
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """List all API keys (metadata only, no secrets)."""
    keys = await db_api_keys.list_api_keys(conn)
    return ApiKeyListResponse(data=[ApiKeyResponse(**k) for k in keys])


@router.get("/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: str,
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """Get details and usage stats for a specific API key."""
    key = await db_api_keys.get_api_key_by_id(conn, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return ApiKeyResponse(**key)


@router.post("/{key_id}/rotate", response_model=ApiKeyCreatedResponse)
async def rotate_api_key(
    key_id: str,
    grace_hours: int = Query(24, ge=0),
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """Rotate an API key. The old key remains valid for the grace period."""
    try:
        result = await api_key_service.rotate_key(
            conn, key_id=key_id, grace_hours=grace_hours
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApiKeyCreatedResponse(**result)


@router.delete("/{key_id}", response_model=MessageResponse)
async def revoke_api_key(
    key_id: str,
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """Immediately revoke an API key."""
    try:
        await api_key_service.revoke_key(conn, key_id=key_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return MessageResponse(message="API key revoked.")
