from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db import audit as db_audit
from app.db import users as db_users
from app.dependencies import get_db, require_admin
from app.models.user import (
    ChangeActiveRequest,
    ChangeRoleRequest,
    PaginationMeta,
    UserListResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["admin"])


# ---------------------------------------------------------------------------
# Admin user management
# ---------------------------------------------------------------------------


@router.get("/auth/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """List all users (paginated). Admin only."""
    users_list, total = await db_users.list_users(conn, page=page, per_page=per_page)
    users = [UserResponse(**u) for u in users_list]
    total_pages = (total + per_page - 1) // per_page
    pagination = PaginationMeta(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
    )
    return UserListResponse(data=users, pagination=pagination)


@router.put("/auth/users/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: str,
    body: ChangeRoleRequest,
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """Change a user's role. Admin only. Logs an audit event."""
    user = await db_users.get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user["role"]
    await db_users.update_user_role(conn, user_id=user_id, role=body.role)
    updated = await db_users.get_user_by_id(conn, user_id)

    # Audit log
    await db_audit.log_event(
        conn,
        user_id=user_id,
        event="role_change",
        details={"old_role": old_role, "new_role": body.role, "changed_by": admin["id"]},
    )

    return UserResponse(**updated)  # type: ignore[arg-type]


@router.put("/auth/users/{user_id}/active", response_model=UserResponse)
async def change_user_active(
    user_id: str,
    body: ChangeActiveRequest,
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """Activate or deactivate a user. Admin only. Logs an audit event."""
    user = await db_users.get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db_users.update_user_active(conn, user_id=user_id, is_active=body.is_active)
    updated = await db_users.get_user_by_id(conn, user_id)

    action = "account_activated" if body.is_active else "account_deactivated"
    await db_audit.log_event(
        conn,
        user_id=user_id,
        event=action,
        details={"changed_by": admin["id"]},
    )

    return UserResponse(**updated)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


@router.get("/admin/audit-log")
async def get_audit_log(
    user_id: str | None = Query(None),
    event: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin),
    conn=Depends(get_db),
):
    """Query the audit log with optional filters. Admin only."""
    entries, total = await db_audit.query_audit_log(
        conn,
        user_id=user_id,
        event=event,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
    )
    return {
        "data": entries,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }
