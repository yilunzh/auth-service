"""Unit tests for app.services.token — JWT and refresh token logic."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest


class TestAccessToken:
    def test_create_and_decode(self):
        from app.services.token import create_access_token, decode_access_token

        token = create_access_token("user-123", "user")
        payload = decode_access_token(token)

        assert payload["sub"] == "user-123"
        assert payload["role"] == "user"
        assert "exp" in payload
        assert "iat" in payload

    def test_expired_token(self):
        from app.config import settings

        payload = {
            "sub": "user-123",
            "role": "user",
            "exp": datetime.utcnow() - timedelta(minutes=1),
            "iat": datetime.utcnow() - timedelta(minutes=16),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        from app.services.token import decode_access_token

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_invalid_token(self):
        from app.services.token import decode_access_token

        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token("not-a-valid-jwt")

    def test_wrong_secret(self):
        payload = {
            "sub": "user-123",
            "role": "user",
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        from app.services.token import decode_access_token

        with pytest.raises(jwt.InvalidSignatureError):
            decode_access_token(token)


class TestRefreshTokenPair:
    async def test_create_pair(self):
        conn = MagicMock()
        with patch("app.services.token.db_tokens") as mock_db:
            mock_db.create_refresh_token = AsyncMock()
            from app.services.token import create_refresh_token_pair

            access, refresh = await create_refresh_token_pair(
                conn, user_id="user-123", role="user"
            )

        assert isinstance(access, str)
        assert isinstance(refresh, str)
        assert len(refresh) > 20
        mock_db.create_refresh_token.assert_awaited_once()

    async def test_refresh_rotation(self):
        """Exchanging a refresh token revokes the old one and issues a new pair."""
        conn = MagicMock()
        old_token_row = {
            "id": "tok-old",
            "user_id": "user-123",
            "user_agent": "TestAgent",
            "ip_address": "127.0.0.1",
        }
        user = {"id": "user-123", "role": "user", "is_active": True}

        with (
            patch("app.services.token.db_tokens") as mock_db,
            patch("app.services.token.db_users") as mock_users,
        ):
            mock_db.get_refresh_token_by_hash = AsyncMock(return_value=old_token_row)
            mock_db.revoke_refresh_token = AsyncMock()
            mock_db.create_refresh_token = AsyncMock()
            mock_users.get_user_by_id = AsyncMock(return_value=user)

            from app.services.token import refresh_access_token

            access, refresh = await refresh_access_token(conn, "raw-old-refresh")

        assert isinstance(access, str)
        assert isinstance(refresh, str)
        mock_db.revoke_refresh_token.assert_awaited_once_with(conn, "tok-old")

    async def test_refresh_invalid_token(self):
        conn = MagicMock()
        with patch("app.services.token.db_tokens") as mock_db:
            mock_db.get_refresh_token_by_hash = AsyncMock(return_value=None)

            from app.services.token import refresh_access_token

            with pytest.raises(ValueError, match="Invalid or expired"):
                await refresh_access_token(conn, "bad-refresh-token")


class TestRevokeToken:
    async def test_revoke_single(self):
        conn = MagicMock()
        token_row = {"id": "tok-1", "user_id": "user-123"}

        with patch("app.services.token.db_tokens") as mock_db:
            mock_db.get_refresh_token_by_hash = AsyncMock(return_value=token_row)
            mock_db.revoke_refresh_token = AsyncMock()

            from app.services.token import revoke_token

            await revoke_token(conn, "raw-refresh", user_id="user-123")

        mock_db.revoke_refresh_token.assert_awaited_once_with(conn, "tok-1")

    async def test_revoke_ownership_check(self):
        conn = MagicMock()
        token_row = {"id": "tok-1", "user_id": "user-123"}

        with patch("app.services.token.db_tokens") as mock_db:
            mock_db.get_refresh_token_by_hash = AsyncMock(return_value=token_row)

            from app.services.token import revoke_token

            with pytest.raises(ValueError, match="does not belong"):
                await revoke_token(conn, "raw-refresh", user_id="other-user")

    async def test_revoke_all(self):
        conn = MagicMock()
        with patch("app.services.token.db_tokens") as mock_db:
            mock_db.revoke_all_user_tokens = AsyncMock(return_value=3)

            from app.services.token import revoke_all_tokens

            count = await revoke_all_tokens(conn, "user-123")

        assert count == 3
        mock_db.revoke_all_user_tokens.assert_awaited_once_with(conn, "user-123")
