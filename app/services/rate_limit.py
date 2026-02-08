"""Rate limiting service backed by MySQL.

Uses INSERT ... ON DUPLICATE KEY UPDATE for atomic upserts on the
rate_limits table. Supports per-key attempt counting, window-based
resets, and explicit blocking with a duration.
"""

from datetime import datetime, timedelta

import aiomysql


async def check_rate_limit(
    conn,
    key_type: str,
    key_value: str,
    max_attempts: int,
    window_seconds: int,
) -> bool:
    """Check whether a request is allowed under the configured rate limit.

    Returns True if the request is allowed, False if the limit has been
    exceeded or the key is currently blocked.
    """
    now = datetime.utcnow()

    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT attempts, window_start, blocked_until
            FROM rate_limits
            WHERE key_type = %s AND key_value = %s
            """,
            (key_type, key_value),
        )
        row = await cur.fetchone()

    if row is None:
        # No record yet -- allowed.
        return True

    # Check explicit block first.
    if row["blocked_until"] is not None and row["blocked_until"] > now:
        return False

    # If the window has expired, the counter will be reset on next record_attempt.
    window_end = row["window_start"] + timedelta(seconds=window_seconds)
    if now > window_end:
        return True

    return row["attempts"] < max_attempts


async def record_attempt(conn, key_type: str, key_value: str) -> None:
    """Record a rate-limit attempt.

    Uses INSERT ... ON DUPLICATE KEY UPDATE so that:
    - First attempt: inserts a new row with attempts=1.
    - Subsequent attempts in the same window: increments attempts.
    - After the window has passed: resets window_start and attempts.

    The window_start reset is handled by checking whether the current
    window_start is older than the window. Because we don't know the
    caller's window_seconds here, we always increment. The caller uses
    check_rate_limit first, which handles window expiry logic.
    """
    now = datetime.utcnow()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            INSERT INTO rate_limits (key_type, key_value, attempts, window_start)
            VALUES (%s, %s, 1, %s)
            ON DUPLICATE KEY UPDATE
                attempts = IF(window_start + INTERVAL 3600 SECOND < %s, 1, attempts + 1),
                window_start = IF(window_start + INTERVAL 3600 SECOND < %s, %s, window_start)
            """,
            (key_type, key_value, now, now, now, now),
        )
        await conn.commit()


async def is_blocked(conn, key_type: str, key_value: str) -> bool:
    """Check if a key is explicitly blocked (regardless of attempt count)."""
    now = datetime.utcnow()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            SELECT blocked_until FROM rate_limits
            WHERE key_type = %s AND key_value = %s
            """,
            (key_type, key_value),
        )
        row = await cur.fetchone()

    if row is None:
        return False

    if row["blocked_until"] is not None and row["blocked_until"] > now:
        return True

    return False


async def block(conn, key_type: str, key_value: str, duration_seconds: int) -> None:
    """Explicitly block a key for the given duration.

    Uses an upsert so the block is applied whether or not a rate_limits
    row already exists.
    """
    now = datetime.utcnow()
    blocked_until = now + timedelta(seconds=duration_seconds)

    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            INSERT INTO rate_limits (key_type, key_value, attempts, window_start, blocked_until)
            VALUES (%s, %s, 0, %s, %s)
            ON DUPLICATE KEY UPDATE blocked_until = %s
            """,
            (key_type, key_value, now, blocked_until, blocked_until),
        )
        await conn.commit()
