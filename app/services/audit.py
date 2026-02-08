"""Audit logging service (fire-and-forget).

Provides a non-blocking interface for recording audit events. Each call
acquires its own connection from the pool so the caller is never blocked.
All errors are swallowed and logged to prevent audit failures from
interrupting application flows.
"""

from __future__ import annotations

import asyncio
import logging

from app.db import audit as db_audit
from app.db.pool import get_connection

logger = logging.getLogger(__name__)


async def _write_event(
    event: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> None:
    """Internal helper that acquires a connection and writes the audit entry.

    Wrapped in try/except so it never propagates exceptions.
    """
    try:
        async with get_connection() as conn:
            await db_audit.log_event(
                conn,
                user_id=user_id,
                event=event,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details,
            )
    except Exception:
        logger.exception("Failed to write audit event: %s (user_id=%s)", event, user_id)


async def log_event(
    event: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> None:
    """Record an audit event in a fire-and-forget fashion.

    Spawns a background task so the caller returns immediately. The task
    acquires its own DB connection, writes the log entry, and releases
    the connection. Any errors are logged but never raised.
    """
    asyncio.create_task(
        _write_event(
            event=event,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
    )
