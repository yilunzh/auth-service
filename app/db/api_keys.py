"""Database layer for API key operations.

All functions are async, take a connection (conn) as the first parameter,
and use parameterized queries with %s placeholders.
"""

from __future__ import annotations

from datetime import datetime

import aiomysql


async def create_api_key(
    conn,
    id: str,
    name: str,
    key_prefix: str,
    key_hash: str,
    created_by: str,
    expires_at: datetime | None = None,
    rate_limit: int | None = None,
) -> dict:
    """Insert a new API key record."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            INSERT INTO api_keys (id, name, key_prefix, key_hash, created_by, expires_at, rate_limit)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (id, name, key_prefix, key_hash, created_by, expires_at, rate_limit),
        )
        await conn.commit()

    return await get_api_key_by_id(conn, id)  # type: ignore[return-value]


async def get_api_key_by_hash(conn, key_hash: str) -> dict | None:
    """Look up an API key by its SHA-256 hash.

    Only returns non-revoked keys. Expiry is checked by the caller so that
    grace-period logic in key rotation can be handled at the service layer.
    """
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT * FROM api_keys
            WHERE key_hash = %s
              AND revoked_at IS NULL
            """,
            (key_hash,),
        )
        return await cur.fetchone()


async def get_api_key_by_id(conn, key_id: str) -> dict | None:
    """Look up an API key by its primary key ID."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT * FROM api_keys WHERE id = %s", (key_id,))
        return await cur.fetchone()


async def list_api_keys(conn) -> list:
    """List all API keys with metadata (no hashes exposed)."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT id, name, key_prefix, created_by, expires_at, revoked_at,
                   last_used_at, usage_count, rate_limit, created_at
            FROM api_keys
            ORDER BY created_at DESC
            """
        )
        return await cur.fetchall()


async def revoke_api_key(conn, key_id: str) -> None:
    """Revoke an API key immediately by setting revoked_at."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "UPDATE api_keys SET revoked_at = %s WHERE id = %s",
            (datetime.utcnow(), key_id),
        )
        await conn.commit()


async def update_api_key_usage(conn, key_id: str) -> None:
    """Increment usage_count and set last_used_at for an API key."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            UPDATE api_keys
            SET usage_count = usage_count + 1, last_used_at = %s
            WHERE id = %s
            """,
            (datetime.utcnow(), key_id),
        )
        await conn.commit()
