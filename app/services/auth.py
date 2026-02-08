"""Authentication business logic.

Orchestrates user registration, login, password management, and email
verification by coordinating the DB layer, password service, token service,
and email service.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

from app.db import tokens as db_tokens
from app.db import users as db_users
from app.services import email as email_service
from app.services import password as password_service
from app.services import token as token_service


def _hash_token(raw_token: str) -> str:
    """Return the hex-encoded SHA-256 hash of a raw token string."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def register_user(conn, email: str, password: str) -> dict:
    """Register a new user account.

    Hashes the password, creates the user record, generates an email
    verification token, and sends the verification email.

    Does NOT return tokens -- the user must verify their email first.

    Raises:
        ValueError: If the email is already registered.
    """
    # Check for existing user
    existing = await db_users.get_user_by_email(conn, email)
    if existing is not None:
        raise ValueError("Email is already registered")

    # Hash password and create user
    pw_hash = await password_service.hash_password(password)
    user_id = str(uuid.uuid4())
    user = await db_users.create_user(conn, id=user_id, email=email, password_hash=pw_hash)

    # Create email verification token
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    token_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)

    await db_tokens.create_email_verification_token(
        conn, id=token_id, user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )

    # Send verification email (fire-and-forget style; errors are logged, not raised)
    await email_service.send_verification_email(to=email, token=raw_token)

    return user


async def login_user(
    conn,
    email: str,
    password: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict:
    """Authenticate a user and return tokens.

    Raises:
        ValueError: On invalid credentials, unverified email, or deactivated account.
    """
    user = await db_users.get_user_by_email(conn, email)
    if user is None:
        raise ValueError("Invalid email or password")

    valid = await password_service.verify_password(password, user["password_hash"])
    if not valid:
        raise ValueError("Invalid email or password")

    if not user.get("is_active"):
        raise ValueError("Account is deactivated")

    if not user.get("is_verified"):
        raise ValueError("Email address has not been verified")

    access_token, refresh_token = await token_service.create_refresh_token_pair(
        conn, user_id=user["id"], role=user["role"], user_agent=user_agent, ip_address=ip_address
    )

    # Strip sensitive fields before returning user data
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": safe_user,
    }


async def change_password(conn, user_id: str, old_password: str, new_password: str) -> None:
    """Change a user's password.

    Verifies the old password, hashes the new one, updates the DB, and
    revokes all existing refresh tokens (forcing re-login on all devices).

    Raises:
        ValueError: If the user is not found or the old password is incorrect.
    """
    user = await db_users.get_user_by_id(conn, user_id)
    if user is None:
        raise ValueError("User not found")

    valid = await password_service.verify_password(old_password, user["password_hash"])
    if not valid:
        raise ValueError("Current password is incorrect")

    new_hash = await password_service.hash_password(new_password)
    await db_users.update_user_password(conn, user_id, new_hash)
    await token_service.revoke_all_tokens(conn, user_id)


async def forgot_password(conn, email: str) -> None:
    """Initiate a password reset flow.

    If a user with the given email exists, creates a reset token and sends
    the reset email. Always completes without error to prevent email
    enumeration.
    """
    user = await db_users.get_user_by_email(conn, email)
    if user is None:
        # Silently return to prevent email enumeration.
        return

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    token_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)

    await db_tokens.create_password_reset_token(
        conn, id=token_id, user_id=user["id"], token_hash=token_hash, expires_at=expires_at
    )

    await email_service.send_password_reset_email(to=email, token=raw_token)


async def reset_password(conn, token: str, new_password: str) -> None:
    """Reset a user's password using a valid reset token.

    Validates the token, hashes the new password, updates the user record,
    marks the token as used, and revokes all existing refresh tokens.

    Raises:
        ValueError: If the token is invalid or expired.
    """
    token_hash = _hash_token(token)
    token_row = await db_tokens.get_reset_token_by_hash(conn, token_hash)
    if token_row is None:
        raise ValueError("Invalid or expired reset token")

    new_hash = await password_service.hash_password(new_password)
    await db_users.update_user_password(conn, token_row["user_id"], new_hash)
    await db_tokens.mark_reset_token_used(conn, token_row["id"])
    await token_service.revoke_all_tokens(conn, token_row["user_id"])


async def verify_email(conn, token: str) -> None:
    """Verify a user's email address using a verification token.

    Raises:
        ValueError: If the token is invalid or expired.
    """
    token_hash = _hash_token(token)
    token_row = await db_tokens.get_verification_token_by_hash(conn, token_hash)
    if token_row is None:
        raise ValueError("Invalid or expired verification token")

    await db_users.set_user_verified(conn, token_row["user_id"])
    await db_tokens.mark_verification_token_used(conn, token_row["id"])
