"""
Rate limiting middleware for API auth endpoints.

Enforces three tiers of rate limits on login, register, and forgot-password:
  - Per-IP: 20 requests per minute
  - Per-email: 10 requests per minute
  - Per-IP+email: 5 requests per minute

Uses the rate_limits table in MySQL via app.db.pool.get_connection.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.db.pool import get_connection

logger = logging.getLogger(__name__)

# Endpoints subject to rate limiting
RATE_LIMITED_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/forgot-password",
}

# Limits: (key_type, max_attempts, window_seconds)
RATE_LIMITS = [
    ("ip", 20, 60),
    ("email", 10, 60),
    ("ip_email", 5, 60),
]


def _get_client_ip(request: Request) -> str:
    """Extract the client IP address, respecting X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Take the first (leftmost) IP — the original client
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def _check_rate_limit(
    conn, key_type: str, key_value: str, max_attempts: int, window_seconds: int
) -> tuple[bool, int]:
    """Check and increment a rate limit counter.

    Returns:
        (is_allowed, retry_after_seconds)
    """
    now = datetime.now(timezone.utc)
    window_start_cutoff = now - timedelta(seconds=window_seconds)

    async with conn.cursor() as cur:
        # Try to get the existing rate limit record
        await cur.execute(
            "SELECT id, attempts, window_start, blocked_until "
            "FROM rate_limits WHERE key_type = %s AND key_value = %s",
            (key_type, key_value),
        )
        row = await cur.fetchone()

        if row is None:
            # No record — create one
            await cur.execute(
                "INSERT INTO rate_limits (key_type, key_value, attempts, window_start) "
                "VALUES (%s, %s, 1, %s)",
                (key_type, key_value, now),
            )
            return (True, 0)

        record_id, attempts, window_start, blocked_until = row

        # Check if currently blocked
        if blocked_until and blocked_until.replace(tzinfo=timezone.utc) > now:
            retry_after = (
                int((blocked_until.replace(tzinfo=timezone.utc) - now).total_seconds()) + 1
            )
            return (False, retry_after)

        # Check if the window has expired — reset
        if window_start.replace(tzinfo=timezone.utc) < window_start_cutoff:
            await cur.execute(
                "UPDATE rate_limits SET attempts = 1, window_start = %s, blocked_until = NULL "
                "WHERE id = %s",
                (now, record_id),
            )
            return (True, 0)

        # Window is still active — increment
        new_attempts = attempts + 1

        if new_attempts > max_attempts:
            # Exceeded limit — block for remainder of window
            remaining = window_seconds - int(
                (now - window_start.replace(tzinfo=timezone.utc)).total_seconds()
            )
            retry_after = max(remaining, 1)
            blocked_until_time = now + timedelta(seconds=retry_after)

            await cur.execute(
                "UPDATE rate_limits SET attempts = %s, blocked_until = %s WHERE id = %s",
                (new_attempts, blocked_until_time, record_id),
            )
            return (False, retry_after)

        # Under the limit — increment
        await cur.execute(
            "UPDATE rate_limits SET attempts = %s WHERE id = %s",
            (new_attempts, record_id),
        )
        return (True, 0)


async def _extract_email_from_body(request: Request) -> str | None:
    """Attempt to extract the email field from a JSON request body.

    Returns None if the body is not JSON or does not contain an email field.
    The body bytes are cached on request.state so downstream handlers can
    still read them.
    """
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        return None

    try:
        body = await request.body()
        data = json.loads(body)
        return data.get("email")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting for authentication API endpoints."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Only rate-limit specific POST endpoints
        if request.method != "POST" or path not in RATE_LIMITED_PATHS:
            return await call_next(request)

        client_ip = _get_client_ip(request)

        # Try to extract email for more granular rate limiting
        email = await _extract_email_from_body(request)

        try:
            async with get_connection() as conn:
                # Check all applicable rate limits
                for key_type, max_attempts, window_seconds in RATE_LIMITS:
                    # Build the key value based on type
                    if key_type == "ip":
                        key_value = client_ip
                    elif key_type == "email":
                        if not email:
                            continue  # Can't check email limit without an email
                        key_value = email.lower()
                    elif key_type == "ip_email":
                        if not email:
                            continue
                        key_value = f"{client_ip}:{email.lower()}"
                    else:
                        continue

                    allowed, retry_after = await _check_rate_limit(
                        conn, key_type, key_value, max_attempts, window_seconds
                    )

                    if not allowed:
                        return JSONResponse(
                            status_code=429,
                            content={
                                "detail": "Too many requests. Please try again later.",
                            },
                            headers={"Retry-After": str(retry_after)},
                        )

        except Exception:
            # If rate limiting fails (e.g., DB down), allow the request through
            # rather than blocking legitimate users. Log the error.
            logger.exception("Rate limit check failed — allowing request through")

        return await call_next(request)
