"""Database layer for token operations.

Handles refresh tokens, email verification tokens, and password reset tokens.
All functions are async, take a connection (conn) as the first parameter,
and use parameterized queries with %s placeholders.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import aiomysql


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------


async def create_refresh_token(
    conn,
    id: str,
    user_id: str,
    token_hash: str,
    expires_at: datetime,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict:
    """Insert a new refresh token record."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, user_agent, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (id, user_id, token_hash, expires_at, user_agent, ip_address),
        )
        await conn.commit()
    return {
        "id": id,
        "user_id": user_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
        "user_agent": user_agent,
        "ip_address": ip_address,
    }


async def get_refresh_token_by_hash(conn, token_hash: str) -> dict | None:
    """Look up a refresh token by its SHA-256 hash.

    Only returns non-revoked, non-expired tokens.
    """
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT * FROM refresh_tokens
            WHERE token_hash = %s
              AND revoked_at IS NULL
              AND expires_at > %s
            """,
            (token_hash, datetime.utcnow()),
        )
        return await cur.fetchone()


async def revoke_refresh_token(conn, token_id: str) -> None:
    """Revoke a single refresh token by ID."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "UPDATE refresh_tokens SET revoked_at = %s WHERE id = %s",
            (datetime.utcnow(), token_id),
        )
        await conn.commit()


async def revoke_all_user_tokens(conn, user_id: str) -> int:
    """Revoke all active refresh tokens for a user.

    Returns the number of tokens revoked.
    """
    now = datetime.utcnow()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            UPDATE refresh_tokens
            SET revoked_at = %s
            WHERE user_id = %s AND revoked_at IS NULL
            """,
            (now, user_id),
        )
        await conn.commit()
        return cur.rowcount


async def list_user_sessions(conn, user_id: str) -> list:
    """List active (non-revoked, non-expired) sessions for a user."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT id, created_at, user_agent, ip_address
            FROM refresh_tokens
            WHERE user_id = %s
              AND revoked_at IS NULL
              AND expires_at > %s
            ORDER BY created_at DESC
            """,
            (user_id, datetime.utcnow()),
        )
        return await cur.fetchall()


# ---------------------------------------------------------------------------
# Email verification tokens
# ---------------------------------------------------------------------------


async def create_email_verification_token(
    conn,
    id: str,
    user_id: str,
    token_hash: str,
    expires_at: datetime,
) -> dict:
    """Insert a new email verification token."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            INSERT INTO email_verification_tokens (id, user_id, token_hash, expires_at)
            VALUES (%s, %s, %s, %s)
            """,
            (id, user_id, token_hash, expires_at),
        )
        await conn.commit()
    return {"id": id, "user_id": user_id, "token_hash": token_hash, "expires_at": expires_at}


async def get_verification_token_by_hash(conn, token_hash: str) -> dict | None:
    """Look up a verification token by hash. Only returns non-used, non-expired tokens."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT * FROM email_verification_tokens
            WHERE token_hash = %s
              AND used_at IS NULL
              AND expires_at > %s
            """,
            (token_hash, datetime.utcnow()),
        )
        return await cur.fetchone()


async def mark_verification_token_used(conn, token_id: str) -> None:
    """Mark a verification token as used."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "UPDATE email_verification_tokens SET used_at = %s WHERE id = %s",
            (datetime.utcnow(), token_id),
        )
        await conn.commit()


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------


async def create_password_reset_token(
    conn,
    id: str,
    user_id: str,
    token_hash: str,
    expires_at: datetime,
) -> dict:
    """Insert a new password reset token."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at)
            VALUES (%s, %s, %s, %s)
            """,
            (id, user_id, token_hash, expires_at),
        )
        await conn.commit()
    return {"id": id, "user_id": user_id, "token_hash": token_hash, "expires_at": expires_at}


async def get_reset_token_by_hash(conn, token_hash: str) -> dict | None:
    """Look up a password reset token by hash. Only returns non-used, non-expired tokens."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT * FROM password_reset_tokens
            WHERE token_hash = %s
              AND used_at IS NULL
              AND expires_at > %s
            """,
            (token_hash, datetime.utcnow()),
        )
        return await cur.fetchone()


async def mark_reset_token_used(conn, token_id: str) -> None:
    """Mark a password reset token as used."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "UPDATE password_reset_tokens SET used_at = %s WHERE id = %s",
            (datetime.utcnow(), token_id),
        )
        await conn.commit()


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


async def cleanup_expired_tokens(conn) -> None:
    """Delete expired tokens from all token tables.

    Removes:
    - Expired refresh tokens (past expires_at)
    - Used or expired verification tokens
    - Used or expired reset tokens
    """
    now = datetime.utcnow()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "DELETE FROM refresh_tokens WHERE expires_at <= %s",
            (now,),
        )
        await cur.execute(
            "DELETE FROM email_verification_tokens WHERE expires_at <= %s OR used_at IS NOT NULL",
            (now,),
        )
        await cur.execute(
            "DELETE FROM password_reset_tokens WHERE expires_at <= %s OR used_at IS NOT NULL",
            (now,),
        )
        await conn.commit()
