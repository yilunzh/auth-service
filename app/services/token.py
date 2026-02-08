"""Token service for JWT access tokens and opaque refresh tokens.

Access tokens are stateless JWTs (HS256, 15-min TTL).
Refresh tokens are random opaque strings stored as SHA-256 hashes in the DB.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

import jwt

from app.config import settings
from app.db import tokens as db_tokens
from app.db import users as db_users


def _hash_token(raw_token: str) -> str:
    """Return the hex-encoded SHA-256 hash of a raw token string."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Access tokens (JWT)
# ---------------------------------------------------------------------------


def create_access_token(user_id: str, role: str) -> str:
    """Create a signed JWT access token.

    Payload: {"sub": user_id, "role": role, "exp": ..., "iat": ...}
    """
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# Refresh tokens (opaque + DB)
# ---------------------------------------------------------------------------


async def create_refresh_token_pair(
    conn,
    user_id: str,
    role: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str]:
    """Generate a new access + refresh token pair.

    The raw refresh token is returned to the client. Only its SHA-256 hash
    is persisted in the database.

    Returns:
        (access_token, raw_refresh_token)
    """
    # Generate opaque refresh token
    raw_refresh = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_refresh)
    token_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await db_tokens.create_refresh_token(
        conn,
        id=token_id,
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    access_token = create_access_token(user_id, role)
    return access_token, raw_refresh


async def refresh_access_token(conn, raw_refresh_token: str) -> tuple[str, str]:
    """Exchange a valid refresh token for a new access + refresh token pair.

    The old refresh token is revoked and a new pair is issued.

    Returns:
        (access_token, raw_refresh_token)

    Raises:
        ValueError: If the refresh token is invalid, expired, or revoked.
    """
    token_hash = _hash_token(raw_refresh_token)
    token_row = await db_tokens.get_refresh_token_by_hash(conn, token_hash)
    if token_row is None:
        raise ValueError("Invalid or expired refresh token")

    # Look up the user to get the current role for the new JWT
    user = await db_users.get_user_by_id(conn, token_row["user_id"])
    if user is None:
        raise ValueError("User not found")
    if not user.get("is_active"):
        raise ValueError("Account is deactivated")

    # Revoke the old token
    await db_tokens.revoke_refresh_token(conn, token_row["id"])

    # Issue a new pair, preserving session metadata
    return await create_refresh_token_pair(
        conn,
        user_id=user["id"],
        role=user["role"],
        user_agent=token_row.get("user_agent"),
        ip_address=token_row.get("ip_address"),
    )


async def revoke_token(conn, token: str, user_id: str | None = None) -> None:
    """Revoke a single refresh token by its raw value.

    Args:
        conn: Database connection.
        token: The raw opaque refresh token string.
        user_id: Optional owner check. If provided, the token must belong
            to this user or a ValueError is raised.

    Raises:
        ValueError: If the token is not found or does not belong to user_id.
    """
    token_hash = _hash_token(token)
    token_row = await db_tokens.get_refresh_token_by_hash(conn, token_hash)
    if token_row is None:
        raise ValueError("Invalid or expired refresh token")

    if user_id is not None and token_row["user_id"] != user_id:
        raise ValueError("Token does not belong to this user")

    await db_tokens.revoke_refresh_token(conn, token_row["id"])


async def revoke_all_tokens(conn, user_id: str) -> int:
    """Revoke all active refresh tokens for a user.

    Returns the number of tokens revoked.
    """
    return await db_tokens.revoke_all_user_tokens(conn, user_id)
