"""API key management service.

Handles creation, validation, rotation, and revocation of API keys.
Keys are prefixed with ``ask_live_`` for easy identification. Only the
SHA-256 hash is stored; the full key is returned once on creation and
never again.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

from app.db import api_keys as db_api_keys


def _hash_key(raw_key: str) -> str:
    """Return the hex-encoded SHA-256 hash of a raw API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def create_key(
    conn,
    name: str,
    created_by: str,
    expires_at: datetime | None = None,
    rate_limit: int | None = None,
) -> dict:
    """Create a new API key.

    Generates a prefixed random key (``ask_live_<random>``), stores its
    SHA-256 hash, and returns the full key to the caller. The full key
    is shown only once.

    Returns:
        dict with keys: id, name, key, key_prefix, expires_at, rate_limit,
        created_by, created_at.
    """
    raw_key = f"ask_live_{secrets.token_urlsafe(32)}"
    key_prefix = raw_key[:16]
    key_hash = _hash_key(raw_key)
    key_id = str(uuid.uuid4())

    row = await db_api_keys.create_api_key(
        conn,
        id=key_id,
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        created_by=created_by,
        expires_at=expires_at,
        rate_limit=rate_limit,
    )

    # Merge the full key into the returned record (shown once only).
    result = dict(row) if row else {}
    result["key"] = raw_key
    return result


async def validate_key(conn, raw_key: str) -> dict | None:
    """Validate an API key and update its usage stats.

    Returns the key record if valid, or None if invalid/expired/revoked.
    """
    key_hash = _hash_key(raw_key)
    row = await db_api_keys.get_api_key_by_hash(conn, key_hash)
    if row is None:
        return None

    # Check expiry (the DB query already filters revoked keys).
    if row.get("expires_at") is not None and row["expires_at"] < datetime.utcnow():
        return None

    # Record usage asynchronously.
    await db_api_keys.update_api_key_usage(conn, row["id"])

    return row


async def rotate_key(conn, key_id: str, grace_hours: int = 24) -> dict:
    """Rotate an API key.

    Creates a new key for the same purpose and sets the old key to expire
    after ``grace_hours`` so that consumers have time to switch over.

    Returns the new key record (including the full key shown once).

    Raises:
        ValueError: If the original key is not found.
    """
    old_row = await db_api_keys.get_api_key_by_id(conn, key_id)
    if old_row is None:
        raise ValueError("API key not found")

    # Create the replacement key, inheriting name/creator/rate_limit.
    new_key = await create_key(
        conn,
        name=old_row["name"],
        created_by=old_row["created_by"],
        expires_at=old_row.get("expires_at"),
        rate_limit=old_row.get("rate_limit"),
    )

    # Set the old key to expire after the grace period.
    grace_expiry = datetime.utcnow() + timedelta(hours=grace_hours)
    async with conn.cursor() as cur:
        await cur.execute(
            "UPDATE api_keys SET expires_at = %s WHERE id = %s",
            (grace_expiry, key_id),
        )
        await conn.commit()

    return new_key


async def revoke_key(conn, key_id: str) -> None:
    """Revoke an API key immediately."""
    await db_api_keys.revoke_api_key(conn, key_id)
