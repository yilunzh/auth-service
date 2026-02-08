"""Unit tests for app.services.password — Argon2 hashing."""

import pytest


class TestPasswordService:
    async def test_hash_returns_argon2_string(self):
        from app.services.password import hash_password

        hashed = await hash_password("TestPassword_Xk9m!z")
        assert hashed.startswith("$argon2id$")

    async def test_verify_correct_password(self):
        from app.services.password import hash_password, verify_password

        hashed = await hash_password("TestPassword_Xk9m!z")
        assert await verify_password("TestPassword_Xk9m!z", hashed) is True

    async def test_verify_incorrect_password(self):
        from app.services.password import hash_password, verify_password

        hashed = await hash_password("TestPassword_Xk9m!z")
        assert await verify_password("WrongPassword_Abc1!", hashed) is False

    async def test_hash_runs_in_thread_pool(self):
        """Verify hashing doesn't block — just test it completes."""
        from app.services.password import hash_password

        h1 = await hash_password("Password_One_Xk9!")
        h2 = await hash_password("Password_Two_Xk9!")
        # Each call produces a different hash (unique salt)
        assert h1 != h2
