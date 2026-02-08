"""Unit tests for app.services.rate_limit — MySQL-backed rate limiting."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_conn_with_cursor(rows=None):
    """Create a mock connection with a cursor that returns the given rows."""
    conn = MagicMock()
    cursor = AsyncMock()
    cursor.fetchone = AsyncMock(return_value=rows)
    cursor.__aenter__ = AsyncMock(return_value=cursor)
    cursor.__aexit__ = AsyncMock(return_value=False)
    conn.cursor.return_value = cursor
    conn.commit = AsyncMock()
    return conn, cursor


class TestCheckRateLimit:
    async def test_allowed_no_record(self):
        """No existing record means the request is allowed."""
        conn, cursor = _make_conn_with_cursor(rows=None)

        from app.services.rate_limit import check_rate_limit

        allowed = await check_rate_limit(conn, "ip", "127.0.0.1", max_attempts=10, window_seconds=60)
        assert allowed is True

    async def test_allowed_under_limit(self):
        """Existing record under the limit allows the request."""
        now = datetime.utcnow()
        row = {"attempts": 3, "window_start": now - timedelta(seconds=10), "blocked_until": None}
        conn, cursor = _make_conn_with_cursor(rows=row)

        from app.services.rate_limit import check_rate_limit

        allowed = await check_rate_limit(conn, "ip", "127.0.0.1", max_attempts=10, window_seconds=60)
        assert allowed is True

    async def test_blocked_over_limit(self):
        """Over the limit blocks the request."""
        now = datetime.utcnow()
        row = {"attempts": 10, "window_start": now - timedelta(seconds=10), "blocked_until": None}
        conn, cursor = _make_conn_with_cursor(rows=row)

        from app.services.rate_limit import check_rate_limit

        allowed = await check_rate_limit(conn, "ip", "127.0.0.1", max_attempts=10, window_seconds=60)
        assert allowed is False

    async def test_blocked_explicit(self):
        """Explicit block (blocked_until in future) blocks the request."""
        now = datetime.utcnow()
        row = {
            "attempts": 1,
            "window_start": now - timedelta(seconds=10),
            "blocked_until": now + timedelta(seconds=30),
        }
        conn, cursor = _make_conn_with_cursor(rows=row)

        from app.services.rate_limit import check_rate_limit

        allowed = await check_rate_limit(conn, "ip", "127.0.0.1", max_attempts=10, window_seconds=60)
        assert allowed is False

    async def test_window_expired_resets(self):
        """Expired window allows the request (counter resets)."""
        now = datetime.utcnow()
        row = {
            "attempts": 99,
            "window_start": now - timedelta(seconds=120),
            "blocked_until": None,
        }
        conn, cursor = _make_conn_with_cursor(rows=row)

        from app.services.rate_limit import check_rate_limit

        allowed = await check_rate_limit(conn, "ip", "127.0.0.1", max_attempts=10, window_seconds=60)
        assert allowed is True


class TestIsBlocked:
    async def test_not_blocked_no_record(self):
        conn, cursor = _make_conn_with_cursor(rows=None)

        from app.services.rate_limit import is_blocked

        assert await is_blocked(conn, "ip", "127.0.0.1") is False

    async def test_blocked_active(self):
        now = datetime.utcnow()
        row = {"blocked_until": now + timedelta(seconds=60)}
        conn, cursor = _make_conn_with_cursor(rows=row)

        from app.services.rate_limit import is_blocked

        assert await is_blocked(conn, "ip", "127.0.0.1") is True
