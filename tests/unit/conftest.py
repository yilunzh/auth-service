"""Unit test fixtures with mocked DB and services."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_db_users():
    """Mock for app.db.users module functions."""
    mock = MagicMock()
    mock.get_user_by_email = AsyncMock()
    mock.get_user_by_id = AsyncMock()
    mock.create_user = AsyncMock()
    mock.update_user_password = AsyncMock()
    mock.set_user_verified = AsyncMock()
    mock.update_user_profile = AsyncMock()
    mock.update_user_role = AsyncMock()
    mock.update_user_active = AsyncMock()
    mock.delete_user = AsyncMock()
    mock.list_users = AsyncMock()
    return mock


@pytest.fixture
def mock_db_tokens():
    """Mock for app.db.tokens module functions."""
    mock = MagicMock()
    mock.create_refresh_token = AsyncMock()
    mock.get_refresh_token_by_hash = AsyncMock()
    mock.revoke_refresh_token = AsyncMock()
    mock.revoke_all_user_tokens = AsyncMock()
    mock.create_email_verification_token = AsyncMock()
    mock.get_verification_token_by_hash = AsyncMock()
    mock.mark_verification_token_used = AsyncMock()
    mock.create_password_reset_token = AsyncMock()
    mock.get_reset_token_by_hash = AsyncMock()
    mock.mark_reset_token_used = AsyncMock()
    mock.list_user_sessions = AsyncMock()
    return mock


@pytest.fixture
def mock_email_service():
    """Mock for app.services.email module."""
    mock = MagicMock()
    mock.send_email = AsyncMock()
    mock.send_verification_email = AsyncMock()
    mock.send_password_reset_email = AsyncMock()
    return mock


@pytest.fixture
def mock_password_service():
    """Mock for app.services.password module."""
    mock = MagicMock()
    mock.hash_password = AsyncMock(return_value="$argon2id$v=19$m=1024,t=1,p=1$fakesalt$fakehash")
    mock.verify_password = AsyncMock(return_value=True)
    return mock


def make_user(
    id="user-123",
    email="test@example.com",
    role="user",
    is_active=True,
    is_verified=True,
    password_hash="$argon2id$v=19$m=1024,t=1,p=1$fakesalt$fakehash",
):
    """Helper to create a user dict for tests."""
    now = datetime.utcnow()
    return {
        "id": id,
        "email": email,
        "role": role,
        "is_active": is_active,
        "is_verified": is_verified,
        "password_hash": password_hash,
        "display_name": None,
        "phone": None,
        "metadata": None,
        "created_at": now,
        "updated_at": now,
    }
