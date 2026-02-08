"""Database layer for audit log operations.

All functions are async, take a connection (conn) as the first parameter,
and use parameterized queries with %s placeholders.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime

import aiomysql


async def log_event(
    conn,
    user_id: str | None,
    event: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> None:
    """Insert a single audit log entry.

    The details dict is serialized to JSON for storage.
    """
    details_json = json.dumps(details) if details is not None else None
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            INSERT INTO audit_log (user_id, event, ip_address, user_agent, details)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, event, ip_address, user_agent, details_json),
        )
        await conn.commit()


async def query_audit_log(
    conn,
    user_id: str | None = None,
    event: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list, int]:
    """Query the audit log with optional filters and pagination.

    Supports dynamic WHERE clauses for user_id, event, and date range.

    Returns:
        (entries, total_count)
    """
    conditions: list[str] = []
    params: list = []

    if user_id is not None:
        conditions.append("user_id = %s")
        params.append(user_id)
    if event is not None:
        conditions.append("event = %s")
        params.append(event)
    if start_date is not None:
        conditions.append("created_at >= %s")
        params.append(start_date)
    if end_date is not None:
        conditions.append("created_at <= %s")
        params.append(end_date)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    offset = (page - 1) * per_page

    async with conn.cursor(aiomysql.DictCursor) as cur:
        # Total count
        await cur.execute(
            f"SELECT COUNT(*) AS cnt FROM audit_log {where_clause}",
            tuple(params),
        )
        total = (await cur.fetchone())["cnt"]

        # Paginated results
        await cur.execute(
            f"SELECT * FROM audit_log {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s",
            tuple(params) + (per_page, offset),
        )
        rows = await cur.fetchall()

    # Deserialize JSON details
    for row in rows:
        if isinstance(row.get("details"), str):
            try:
                row["details"] = json.loads(row["details"])
            except (json.JSONDecodeError, TypeError):
                pass

    return rows, total
