"""Health check endpoint.

Verifies the application is running and the database pool is reachable.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.db.pool import get_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return service health status and current timestamp.

    Performs a lightweight ``SELECT 1`` against the database to confirm
    pool connectivity.  Returns ``"healthy"`` when the DB responds and
    ``"degraded"`` (HTTP 200 still) when the DB is unreachable so that
    load-balancer probes can distinguish the two states.
    """
    db_ok = False
    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                db_ok = True
    except Exception:  # nosec B110
        pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected" if db_ok else "unreachable",
    }
