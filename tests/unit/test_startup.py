"""Unit tests for JWT secret validation at startup."""

import logging
from unittest.mock import patch

import pytest


class TestValidateJwtSecret:
    def test_default_secret_debug_true_logs_warning(self, caplog):
        """Default secret + DEBUG=True should log a warning but not raise."""
        from app.main import _DEFAULT_JWT_SECRET, _validate_jwt_secret

        mock_settings = type(
            "S",
            (),
            {
                "JWT_SECRET_KEY": _DEFAULT_JWT_SECRET,
                "DEBUG": True,
            },
        )()

        with patch("app.main.settings", mock_settings):
            with caplog.at_level(logging.WARNING, logger="app.main"):
                _validate_jwt_secret()

        assert "default value" in caplog.text

    def test_default_secret_debug_false_raises(self):
        """Default secret + DEBUG=False should raise RuntimeError."""
        from app.main import _DEFAULT_JWT_SECRET, _validate_jwt_secret

        mock_settings = type(
            "S",
            (),
            {
                "JWT_SECRET_KEY": _DEFAULT_JWT_SECRET,
                "DEBUG": False,
            },
        )()

        with patch("app.main.settings", mock_settings):
            with pytest.raises(RuntimeError, match="default value"):
                _validate_jwt_secret()

    def test_empty_secret_raises(self):
        """Empty secret should raise RuntimeError."""
        from app.main import _validate_jwt_secret

        mock_settings = type(
            "S",
            (),
            {
                "JWT_SECRET_KEY": "",
                "DEBUG": False,
            },
        )()

        with patch("app.main.settings", mock_settings):
            with pytest.raises(RuntimeError, match="at least 16 characters"):
                _validate_jwt_secret()

    def test_short_secret_raises(self):
        """Secret shorter than 16 chars should raise RuntimeError."""
        from app.main import _validate_jwt_secret

        mock_settings = type(
            "S",
            (),
            {
                "JWT_SECRET_KEY": "short",
                "DEBUG": False,
            },
        )()

        with patch("app.main.settings", mock_settings):
            with pytest.raises(RuntimeError, match="at least 16 characters"):
                _validate_jwt_secret()

    def test_valid_secret_passes(self):
        """A proper secret (>= 16 chars, not default) should pass."""
        from app.main import _validate_jwt_secret

        mock_settings = type(
            "S",
            (),
            {
                "JWT_SECRET_KEY": "a-very-strong-secret-key-for-production",
                "DEBUG": False,
            },
        )()

        with patch("app.main.settings", mock_settings):
            _validate_jwt_secret()  # Should not raise
