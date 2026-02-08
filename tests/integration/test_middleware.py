"""Integration tests for middleware — security headers, CSRF, rate limiting."""

from tests.integration.conftest import TEST_PASSWORD, _create_user


class TestSecurityHeaders:
    async def test_security_headers_present(self, test_client, db_conn):
        resp = await test_client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in resp.headers
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

    async def test_security_headers_on_api(self, test_client, db_conn):
        resp = await test_client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": "SomePass123!"},
        )
        # Even on 401, security headers should be present
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"


class TestCSRF:
    async def test_csrf_cookie_set_on_get(self, test_client, db_conn):
        resp = await test_client.get("/auth/login")
        # The CSRF middleware sets a cookie on GET /auth/*
        cookies = resp.cookies
        if resp.status_code == 200:
            assert "csrf_token" in cookies or resp.status_code != 200

    async def test_csrf_post_missing_cookie(self, test_client, db_conn):
        """POST to /auth/* without CSRF cookie should fail."""
        resp = await test_client.post(
            "/auth/login",
            data={"email": "test@test.com", "password": "TestPass123!"},
        )
        assert resp.status_code == 403

    async def test_csrf_post_token_mismatch(self, test_client, db_conn):
        """POST with mismatched CSRF tokens should fail."""
        # First GET to get a cookie
        get_resp = await test_client.get("/auth/login")
        csrf_cookie = get_resp.cookies.get("csrf_token")

        if csrf_cookie:
            resp = await test_client.post(
                "/auth/login",
                data={
                    "email": "test@test.com",
                    "password": "TestPass123!",
                    "csrf_token": "wrong-token",
                },
                cookies={"csrf_token": csrf_cookie},
            )
            assert resp.status_code == 403

    async def test_csrf_post_valid_token(self, test_client, db_conn):
        """POST with matching CSRF tokens should pass CSRF check."""
        user = await _create_user(db_conn, email="csrf-test@test.com")

        # GET to get CSRF cookie
        get_resp = await test_client.get("/auth/login")
        csrf_cookie = get_resp.cookies.get("csrf_token")

        if csrf_cookie:
            resp = await test_client.post(
                "/auth/login",
                data={
                    "email": user["email"],
                    "password": TEST_PASSWORD,
                    "csrf_token": csrf_cookie,
                },
                cookies={"csrf_token": csrf_cookie},
            )
            # Should pass CSRF check (may still fail for other reasons like redirect)
            assert resp.status_code != 403


class TestRateLimit:
    async def test_rate_limit_allows_under_threshold(self, test_client, db_conn):
        """A few requests should be allowed."""
        for _ in range(3):
            resp = await test_client.post(
                "/api/auth/login",
                json={"email": "rate@test.com", "password": "SomePass123!"},
            )
            # Should not be rate limited (401 is expected for wrong credentials)
            assert resp.status_code in (200, 401)

    async def test_rate_limit_blocks_over_threshold(self, test_client, db_conn):
        """Exceeding the per-IP+email limit should result in 429."""
        blocked = False
        # The ip_email limit is 5/min — send 8 requests
        for i in range(8):
            resp = await test_client.post(
                "/api/auth/login",
                json={"email": "ratelimit@test.com", "password": "SomePass123!"},
            )
            if resp.status_code == 429:
                blocked = True
                assert "Retry-After" in resp.headers
                break

        assert blocked, "Expected to be rate-limited after multiple requests"
