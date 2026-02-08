"""Unit tests for breached password Bloom filter."""

import tempfile
from pathlib import Path

import pytest

from app.services.breach_check import init_bloom_filter, is_breached, reset


@pytest.fixture(autouse=True)
def _reset_filter():
    """Reset the Bloom filter before each test."""
    reset()
    yield
    reset()


@pytest.fixture
def breach_file(tmp_path):
    """Create a temporary breached passwords file."""
    passwords = [
        "password",
        "123456",
        "12345678",
        "qwerty",
        "abc123",
        "monkey",
        "letmein",
        "dragon",
        "111111",
        "baseball",
    ]
    path = tmp_path / "breached.txt"
    path.write_text("\n".join(passwords))
    return path


class TestBloomFilter:
    def test_filter_loads(self, breach_file):
        count = init_bloom_filter(breach_file)
        assert count == 10

    def test_common_passwords_detected(self, breach_file):
        init_bloom_filter(breach_file)
        assert is_breached("password") is True
        assert is_breached("123456") is True
        assert is_breached("qwerty") is True

    def test_unique_password_passes(self, breach_file):
        init_bloom_filter(breach_file)
        assert is_breached("TestPassword_Xk9m!z") is False
        assert is_breached("V3ry$ecure#P@ssw0rd_2024!") is False

    def test_case_insensitive(self, breach_file):
        init_bloom_filter(breach_file)
        assert is_breached("PASSWORD") is True
        assert is_breached("Password") is True
        assert is_breached("QWERTY") is True

    def test_not_initialized_returns_false(self):
        """Fail-open: if filter isn't loaded, allow all passwords."""
        assert is_breached("password") is False
        assert is_breached("123456") is False

    def test_idempotent_init(self, breach_file):
        count1 = init_bloom_filter(breach_file)
        count2 = init_bloom_filter(breach_file)
        assert count1 == 10
        assert count2 == 0  # Second call is a no-op

    def test_missing_file_returns_zero(self, tmp_path):
        count = init_bloom_filter(tmp_path / "nonexistent.txt")
        assert count == 0
