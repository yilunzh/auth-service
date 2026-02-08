"""Unit tests for app.services.auth — business logic with mocked DB."""

from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

import pytest

from tests.unit.conftest import make_user


@pytest.fixture
def conn():
    return MagicMock()


class TestRegisterUser:
    async def test_register_success(self, conn, mock_db_users, mock_password_service, mock_email_service):
        mock_db_users.get_user_by_email.return_value = None
        mock_db_users.create_user.return_value = make_user(is_verified=False)

        with (
            patch("app.services.auth.db_users", mock_db_users),
            patch("app.services.auth.password_service", mock_password_service),
            patch("app.services.auth.email_service", mock_email_service),
            patch("app.services.auth.db_tokens") as mock_db_tokens,
        ):
            mock_db_tokens.create_email_verification_token = AsyncMock()
            from app.services.auth import register_user

            result = await register_user(conn, "test@example.com", "TestPassword_Xk9m!z")

        assert result["email"] == "test@example.com"
        mock_password_service.hash_password.assert_awaited_once()
        mock_db_users.create_user.assert_awaited_once()
        mock_email_service.send_verification_email.assert_awaited_once()

    async def test_register_duplicate_email(self, conn, mock_db_users):
        mock_db_users.get_user_by_email.return_value = make_user()

        with patch("app.services.auth.db_users", mock_db_users):
            from app.services.auth import register_user

            with pytest.raises(ValueError, match="already registered"):
                await register_user(conn, "test@example.com", "TestPassword_Xk9m!z")


class TestLoginUser:
    async def test_login_success(self, conn, mock_db_users, mock_password_service):
        user = make_user()
        mock_db_users.get_user_by_email.return_value = user
        mock_password_service.verify_password.return_value = True

        with (
            patch("app.services.auth.db_users", mock_db_users),
            patch("app.services.auth.password_service", mock_password_service),
            patch("app.services.auth.token_service") as mock_token_svc,
        ):
            mock_token_svc.create_refresh_token_pair = AsyncMock(
                return_value=("access_tok", "refresh_tok")
            )
            from app.services.auth import login_user

            result = await login_user(conn, "test@example.com", "TestPassword_Xk9m!z")

        assert result["access_token"] == "access_tok"
        assert result["refresh_token"] == "refresh_tok"
        assert "password_hash" not in result["user"]

    async def test_login_wrong_password(self, conn, mock_db_users, mock_password_service):
        mock_db_users.get_user_by_email.return_value = make_user()
        mock_password_service.verify_password.return_value = False

        with (
            patch("app.services.auth.db_users", mock_db_users),
            patch("app.services.auth.password_service", mock_password_service),
        ):
            from app.services.auth import login_user

            with pytest.raises(ValueError, match="Invalid email or password"):
                await login_user(conn, "test@example.com", "WrongPassword123!")

    async def test_login_user_not_found(self, conn, mock_db_users):
        mock_db_users.get_user_by_email.return_value = None

        with patch("app.services.auth.db_users", mock_db_users):
            from app.services.auth import login_user

            with pytest.raises(ValueError, match="Invalid email or password"):
                await login_user(conn, "nobody@example.com", "TestPassword_Xk9m!z")

    async def test_login_unverified(self, conn, mock_db_users, mock_password_service):
        mock_db_users.get_user_by_email.return_value = make_user(is_verified=False)
        mock_password_service.verify_password.return_value = True

        with (
            patch("app.services.auth.db_users", mock_db_users),
            patch("app.services.auth.password_service", mock_password_service),
        ):
            from app.services.auth import login_user

            with pytest.raises(ValueError, match="not been verified"):
                await login_user(conn, "test@example.com", "TestPassword_Xk9m!z")

    async def test_login_deactivated(self, conn, mock_db_users, mock_password_service):
        mock_db_users.get_user_by_email.return_value = make_user(is_active=False)
        mock_password_service.verify_password.return_value = True

        with (
            patch("app.services.auth.db_users", mock_db_users),
            patch("app.services.auth.password_service", mock_password_service),
        ):
            from app.services.auth import login_user

            with pytest.raises(ValueError, match="deactivated"):
                await login_user(conn, "test@example.com", "TestPassword_Xk9m!z")


class TestChangePassword:
    async def test_change_password_success(self, conn, mock_db_users, mock_password_service):
        mock_db_users.get_user_by_id.return_value = make_user()
        mock_password_service.verify_password.return_value = True

        with (
            patch("app.services.auth.db_users", mock_db_users),
            patch("app.services.auth.password_service", mock_password_service),
            patch("app.services.auth.token_service") as mock_token_svc,
        ):
            mock_token_svc.revoke_all_tokens = AsyncMock()
            from app.services.auth import change_password

            await change_password(conn, "user-123", "OldPass_Xk9m!z", "NewPass_Xk9m!z")

        mock_db_users.update_user_password.assert_awaited_once()
        mock_token_svc.revoke_all_tokens.assert_awaited_once_with(conn, "user-123")

    async def test_change_password_wrong_old(self, conn, mock_db_users, mock_password_service):
        mock_db_users.get_user_by_id.return_value = make_user()
        mock_password_service.verify_password.return_value = False

        with (
            patch("app.services.auth.db_users", mock_db_users),
            patch("app.services.auth.password_service", mock_password_service),
        ):
            from app.services.auth import change_password

            with pytest.raises(ValueError, match="incorrect"):
                await change_password(conn, "user-123", "WrongOld!z", "NewPass_Xk9m!z")


class TestForgotPassword:
    async def test_forgot_password_existing_user(self, conn, mock_db_users, mock_email_service):
        mock_db_users.get_user_by_email.return_value = make_user()

        with (
            patch("app.services.auth.db_users", mock_db_users),
            patch("app.services.auth.email_service", mock_email_service),
            patch("app.services.auth.db_tokens") as mock_db_tokens,
        ):
            mock_db_tokens.create_password_reset_token = AsyncMock()
            from app.services.auth import forgot_password

            await forgot_password(conn, "test@example.com")

        mock_email_service.send_password_reset_email.assert_awaited_once()

    async def test_forgot_password_nonexistent_user(self, conn, mock_db_users, mock_email_service):
        mock_db_users.get_user_by_email.return_value = None

        with (
            patch("app.services.auth.db_users", mock_db_users),
            patch("app.services.auth.email_service", mock_email_service),
        ):
            from app.services.auth import forgot_password

            # Should not raise
            await forgot_password(conn, "nobody@example.com")

        mock_email_service.send_password_reset_email.assert_not_awaited()


class TestResetPassword:
    async def test_reset_password_success(self, conn, mock_password_service):
        token_row = {"id": "tok-1", "user_id": "user-123"}

        with (
            patch("app.services.auth.password_service", mock_password_service),
            patch("app.services.auth.db_tokens") as mock_db_tokens,
            patch("app.services.auth.db_users") as mock_db_users_local,
            patch("app.services.auth.token_service") as mock_token_svc,
        ):
            mock_db_tokens.get_reset_token_by_hash = AsyncMock(return_value=token_row)
            mock_db_tokens.mark_reset_token_used = AsyncMock()
            mock_db_users_local.update_user_password = AsyncMock()
            mock_token_svc.revoke_all_tokens = AsyncMock()
            from app.services.auth import reset_password

            await reset_password(conn, "raw-token-value", "NewPass_Xk9m!z")

        mock_db_users_local.update_user_password.assert_awaited_once()
        mock_db_tokens.mark_reset_token_used.assert_awaited_once()

    async def test_reset_password_invalid_token(self, conn):
        with patch("app.services.auth.db_tokens") as mock_db_tokens:
            mock_db_tokens.get_reset_token_by_hash = AsyncMock(return_value=None)
            from app.services.auth import reset_password

            with pytest.raises(ValueError, match="Invalid or expired"):
                await reset_password(conn, "bad-token", "NewPass_Xk9m!z")


class TestVerifyEmail:
    async def test_verify_email_success(self, conn):
        token_row = {"id": "tok-1", "user_id": "user-123"}

        with (
            patch("app.services.auth.db_tokens") as mock_db_tokens,
            patch("app.services.auth.db_users") as mock_db_users_local,
        ):
            mock_db_tokens.get_verification_token_by_hash = AsyncMock(return_value=token_row)
            mock_db_tokens.mark_verification_token_used = AsyncMock()
            mock_db_users_local.set_user_verified = AsyncMock()
            from app.services.auth import verify_email

            await verify_email(conn, "raw-verify-token")

        mock_db_users_local.set_user_verified.assert_awaited_once_with(conn, "user-123")

    async def test_verify_email_invalid_token(self, conn):
        with patch("app.services.auth.db_tokens") as mock_db_tokens:
            mock_db_tokens.get_verification_token_by_hash = AsyncMock(return_value=None)
            from app.services.auth import verify_email

            with pytest.raises(ValueError, match="Invalid or expired"):
                await verify_email(conn, "bad-token")
