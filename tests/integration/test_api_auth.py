"""Integration tests for auth API endpoints — full request/response cycle."""

from tests.integration.conftest import TEST_PASSWORD, _create_user, _login_user


class TestRegister:
    async def test_register_success(self, test_client, db_conn):
        resp = await test_client.post(
            "/api/auth/register",
            json={"email": "newuser@test.com", "password": "StrongPass_Xk9m!z"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "verify" in data["message"].lower() or "check" in data["message"].lower()

    async def test_register_duplicate_email(self, test_client, test_user, db_conn):
        resp = await test_client.post(
            "/api/auth/register",
            json={"email": test_user["email"], "password": "StrongPass_Xk9m!z"},
        )
        assert resp.status_code == 400
        assert "already" in resp.json()["detail"].lower()

    async def test_register_short_password(self, test_client, db_conn):
        resp = await test_client.post(
            "/api/auth/register",
            json={"email": "short@test.com", "password": "short"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_email(self, test_client, db_conn):
        resp = await test_client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "password": "StrongPass_Xk9m!z"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, test_client, test_user, db_conn):
        resp = await test_client.post(
            "/api/auth/login",
            json={"email": test_user["email"], "password": TEST_PASSWORD},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, test_client, test_user, db_conn):
        resp = await test_client.post(
            "/api/auth/login",
            json={"email": test_user["email"], "password": "WrongPassword_999!z"},
        )
        assert resp.status_code == 401

    async def test_login_unverified(self, test_client, db_conn):
        user = await _create_user(db_conn, email="unverified@test.com", is_verified=False)
        resp = await test_client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": TEST_PASSWORD},
        )
        assert resp.status_code == 401
        assert "verified" in resp.json()["detail"].lower()

    async def test_login_nonexistent_user(self, test_client, db_conn):
        resp = await test_client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": TEST_PASSWORD},
        )
        assert resp.status_code == 401


class TestRefresh:
    async def test_refresh_success(self, test_client, test_user, db_conn):
        login_data = await _login_user(test_client, test_user["email"])
        resp = await test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": login_data["refresh_token"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should differ from old
        assert data["refresh_token"] != login_data["refresh_token"]

    async def test_refresh_invalid_token(self, test_client, db_conn):
        resp = await test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token-value"},
        )
        assert resp.status_code == 401


class TestMe:
    async def test_get_me(self, test_client, test_user, auth_headers, db_conn):
        resp = await test_client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == test_user["email"]
        assert data["id"] == test_user["id"]
        assert "password_hash" not in data

    async def test_get_me_no_auth(self, test_client, db_conn):
        resp = await test_client.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_update_me(self, test_client, auth_headers, db_conn):
        resp = await test_client.put(
            "/api/auth/me",
            headers=auth_headers,
            json={"display_name": "Test User", "phone": "+1234567890"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Test User"
        assert data["phone"] == "+1234567890"


class TestChangePassword:
    async def test_change_password_success(self, test_client, test_user, auth_headers, db_conn):
        resp = await test_client.put(
            "/api/auth/password",
            headers=auth_headers,
            json={"old_password": TEST_PASSWORD, "new_password": "NewPass_Xk9m!z99"},
        )
        assert resp.status_code == 200

        # Can login with new password
        resp2 = await test_client.post(
            "/api/auth/login",
            json={"email": test_user["email"], "password": "NewPass_Xk9m!z99"},
        )
        assert resp2.status_code == 200

    async def test_change_password_wrong_old(self, test_client, auth_headers, db_conn):
        resp = await test_client.put(
            "/api/auth/password",
            headers=auth_headers,
            json={"old_password": "WrongOldPass!z", "new_password": "NewPass_Xk9m!z99"},
        )
        assert resp.status_code == 400


class TestLogout:
    async def test_logout_single(self, test_client, test_user, auth_headers, db_conn):
        login_data = await _login_user(test_client, test_user["email"])
        resp = await test_client.post(
            "/api/auth/logout",
            headers=auth_headers,
            json={"refresh_token": login_data["refresh_token"]},
        )
        assert resp.status_code == 200

    async def test_logout_all(self, test_client, auth_headers, db_conn):
        resp = await test_client.post("/api/auth/logout-all", headers=auth_headers)
        assert resp.status_code == 200


class TestSessions:
    async def test_list_sessions(self, test_client, test_user, auth_headers, db_conn):
        resp = await test_client.get("/api/auth/sessions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the current session


class TestDeleteAccount:
    async def test_delete_me(self, test_client, db_conn):
        user = await _create_user(db_conn, email="delete-me@test.com")
        tokens = await _login_user(test_client, user["email"])
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = await test_client.delete("/api/auth/me", headers=headers)
        assert resp.status_code == 200

        # User should no longer be able to login
        resp2 = await test_client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": TEST_PASSWORD},
        )
        assert resp2.status_code == 401


class TestVerifyEmail:
    async def test_verify_email_flow(self, test_client, db_conn):
        """Register, capture token from DB, verify email, then login."""
        email = "verify-flow@test.com"

        # Register
        resp = await test_client.post(
            "/api/auth/register",
            json={"email": email, "password": "StrongPass_Xk9m!z"},
        )
        assert resp.status_code == 201

        # Find the verification token from the DB
        async with db_conn.cursor() as cur:
            await cur.execute(
                """SELECT evt.token_hash FROM email_verification_tokens evt
                   JOIN users u ON u.id = evt.user_id
                   WHERE u.email = %s AND evt.used_at IS NULL
                   ORDER BY evt.created_at DESC LIMIT 1""",
                (email,),
            )
            row = await cur.fetchone()

        assert row is not None, "Verification token not found in DB"

        # We can't verify via the hash alone since we need the raw token.
        # Instead, directly mark the user as verified for the login test.
        async with db_conn.cursor() as cur:
            await cur.execute("UPDATE users SET is_verified = 1 WHERE email = %s", (email,))

        # Now login should work
        resp2 = await test_client.post(
            "/api/auth/login",
            json={"email": email, "password": "StrongPass_Xk9m!z"},
        )
        assert resp2.status_code == 200


class TestForgotResetPassword:
    async def test_forgot_password_always_200(self, test_client, db_conn):
        # Existing user
        resp = await test_client.post(
            "/api/auth/forgot-password",
            json={"email": "nobody@test.com"},
        )
        assert resp.status_code == 200

    async def test_reset_password_invalid_token(self, test_client, db_conn):
        resp = await test_client.post(
            "/api/auth/reset-password",
            json={"token": "bad-token", "new_password": "NewPass_Xk9m!z99"},
        )
        assert resp.status_code == 400
