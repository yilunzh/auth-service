"""Unit tests for rate limit middleware — fail-open vs fail-closed behaviour."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.main import app


@pytest.fixture
async def client():
    """Async HTTP test client."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


def _patch_rate_limit_connection_error():
    """Mock get_connection *only in the rate_limit module* to raise."""
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(side_effect=RuntimeError("DB down"))
    cm.__aexit__ = AsyncMock()
    return patch("app.middleware.rate_limit.get_connection", return_value=cm)


@asynccontextmanager
async def _fake_pool_connection():
    """Yield a mock connection so the handler's get_db dependency doesn't crash."""
    conn = MagicMock()
    cursor = AsyncMock()
    cursor.fetchone = AsyncMock(return_value=None)
    cursor.__aenter__ = AsyncMock(return_value=cursor)
    cursor.__aexit__ = AsyncMock(return_value=False)
    conn.cursor = MagicMock(return_value=cursor)
    yield conn


class TestFailOpenClosed:
    async def test_fail_open_allows_request(self, client):
        """When fail_open=True and DB fails, rate limiter should not block."""
        with (
            _patch_rate_limit_connection_error(),
            patch("app.db.pool.get_connection", _fake_pool_connection),
            patch("app.dependencies.get_connection", _fake_pool_connection),
            patch("app.middleware.rate_limit.settings") as mock_settings,
        ):
            mock_settings.RATE_LIMIT_FAIL_OPEN = True
            resp = await client.post(
                "/api/auth/login",
                json={"email": "test@example.com", "password": "SomePass123!"},
            )
            # Rate limiter should NOT return 503; request passes through.
            # Handler returns 401 (user not found) — the important thing is no 503.
            assert resp.status_code != 503

    async def test_fail_closed_returns_503(self, client):
        """When fail_open=False and DB fails, request should get 503."""
        with (
            _patch_rate_limit_connection_error(),
            patch("app.middleware.rate_limit.settings") as mock_settings,
        ):
            mock_settings.RATE_LIMIT_FAIL_OPEN = False
            resp = await client.post(
                "/api/auth/login",
                json={"email": "test@example.com", "password": "SomePass123!"},
            )
            assert resp.status_code == 503
            assert "temporarily unavailable" in resp.json()["detail"].lower()

    async def test_non_rate_limited_path_unaffected(self, client):
        """Non-rate-limited paths should not be affected by fail-closed mode."""
        with (
            _patch_rate_limit_connection_error(),
            patch("app.middleware.rate_limit.settings") as mock_settings,
        ):
            mock_settings.RATE_LIMIT_FAIL_OPEN = False
            resp = await client.get("/health")
            # Health endpoint is not rate-limited, should work fine
            assert resp.status_code != 503
