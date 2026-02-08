"""Unit tests for app.services.api_key — API key lifecycle."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_key_row(**overrides):
    base = {
        "id": "key-1",
        "name": "test-key",
        "key_prefix": "ask_live_abcdef",
        "key_hash": "abc123hash",
        "created_by": "admin-1",
        "expires_at": None,
        "revoked_at": None,
        "last_used_at": None,
        "usage_count": 0,
        "rate_limit": None,
        "created_at": datetime.utcnow(),
    }
    base.update(overrides)
    return base


class TestCreateKey:
    async def test_create_returns_full_key(self):
        conn = MagicMock()
        row = _make_key_row()

        with patch("app.services.api_key.db_api_keys") as mock_db:
            mock_db.create_api_key = AsyncMock(return_value=row)
            from app.services.api_key import create_key

            result = await create_key(conn, name="my-key", created_by="admin-1")

        assert result["key"].startswith("ask_live_")
        assert len(result["key"]) > 16
        mock_db.create_api_key.assert_awaited_once()

    async def test_key_prefix_format(self):
        conn = MagicMock()
        row = _make_key_row()

        with patch("app.services.api_key.db_api_keys") as mock_db:
            mock_db.create_api_key = AsyncMock(return_value=row)
            from app.services.api_key import create_key

            result = await create_key(conn, name="my-key", created_by="admin-1")

        # The key_prefix passed to DB should be first 16 chars of generated key
        call_kwargs = mock_db.create_api_key.call_args
        stored_prefix = call_kwargs.kwargs.get("key_prefix") or call_kwargs[1].get("key_prefix")
        assert result["key"][:16] == stored_prefix


class TestValidateKey:
    async def test_validate_valid_key(self):
        conn = MagicMock()
        row = _make_key_row()

        with patch("app.services.api_key.db_api_keys") as mock_db:
            mock_db.get_api_key_by_hash = AsyncMock(return_value=row)
            mock_db.update_api_key_usage = AsyncMock()
            from app.services.api_key import validate_key

            result = await validate_key(conn, "ask_live_somerawkey")

        assert result is not None
        assert result["id"] == "key-1"

    async def test_validate_expired_key(self):
        conn = MagicMock()
        row = _make_key_row(expires_at=datetime.utcnow() - timedelta(hours=1))

        with patch("app.services.api_key.db_api_keys") as mock_db:
            mock_db.get_api_key_by_hash = AsyncMock(return_value=row)
            from app.services.api_key import validate_key

            result = await validate_key(conn, "ask_live_expired")

        assert result is None

    async def test_validate_not_found(self):
        conn = MagicMock()

        with patch("app.services.api_key.db_api_keys") as mock_db:
            mock_db.get_api_key_by_hash = AsyncMock(return_value=None)
            from app.services.api_key import validate_key

            result = await validate_key(conn, "ask_live_nonexistent")

        assert result is None


class TestRotateKey:
    async def test_rotate_creates_new_key(self):
        conn = MagicMock()
        old_row = _make_key_row()
        new_row = _make_key_row(id="key-2")

        with patch("app.services.api_key.db_api_keys") as mock_db:
            mock_db.get_api_key_by_id = AsyncMock(return_value=old_row)
            mock_db.create_api_key = AsyncMock(return_value=new_row)
            # Mock the cursor for the UPDATE
            mock_cursor = AsyncMock()
            conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
            conn.cursor.return_value.__aexit__ = AsyncMock(return_value=False)
            conn.commit = AsyncMock()

            from app.services.api_key import rotate_key

            result = await rotate_key(conn, "key-1", grace_hours=24)

        assert result["key"].startswith("ask_live_")

    async def test_rotate_not_found(self):
        conn = MagicMock()

        with patch("app.services.api_key.db_api_keys") as mock_db:
            mock_db.get_api_key_by_id = AsyncMock(return_value=None)
            from app.services.api_key import rotate_key

            with pytest.raises(ValueError, match="not found"):
                await rotate_key(conn, "nonexistent-key")


class TestRevokeKey:
    async def test_revoke(self):
        conn = MagicMock()

        with patch("app.services.api_key.db_api_keys") as mock_db:
            mock_db.revoke_api_key = AsyncMock()
            from app.services.api_key import revoke_key

            await revoke_key(conn, "key-1")

        mock_db.revoke_api_key.assert_awaited_once_with(conn, "key-1")
