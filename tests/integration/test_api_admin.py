"""Integration tests for admin API endpoints."""

import pytest

from tests.integration.conftest import TEST_PASSWORD, _create_user, _login_user


class TestListUsers:
    async def test_list_users_paginated(self, test_client, admin_headers, test_user, db_conn):
        resp = await test_client.get("/api/auth/users", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["total"] >= 2  # admin + test_user

    async def test_list_users_non_admin(self, test_client, auth_headers, db_conn):
        resp = await test_client.get("/api/auth/users", headers=auth_headers)
        assert resp.status_code == 403


class TestChangeRole:
    async def test_change_role(self, test_client, admin_headers, test_user, db_conn):
        resp = await test_client.put(
            f"/api/auth/users/{test_user['id']}/role",
            headers=admin_headers,
            json={"role": "admin"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

        # Verify audit log entry
        resp2 = await test_client.get(
            "/api/admin/audit-log",
            headers=admin_headers,
            params={"event": "role_change", "user_id": test_user["id"]},
        )
        assert resp2.status_code == 200
        entries = resp2.json()["data"]
        assert len(entries) >= 1
        assert entries[0]["event"] == "role_change"

    async def test_change_role_non_admin(self, test_client, auth_headers, test_user, db_conn):
        resp = await test_client.put(
            f"/api/auth/users/{test_user['id']}/role",
            headers=auth_headers,
            json={"role": "admin"},
        )
        assert resp.status_code == 403


class TestChangeActive:
    async def test_deactivate_user(self, test_client, admin_headers, db_conn):
        user = await _create_user(db_conn, email="deactivate-me@test.com")
        resp = await test_client.put(
            f"/api/auth/users/{user['id']}/active",
            headers=admin_headers,
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        # Verify audit log
        resp2 = await test_client.get(
            "/api/admin/audit-log",
            headers=admin_headers,
            params={"event": "account_deactivated"},
        )
        assert resp2.status_code == 200
        assert len(resp2.json()["data"]) >= 1

    async def test_activate_user(self, test_client, admin_headers, db_conn):
        user = await _create_user(db_conn, email="activate-me@test.com", is_active=False)
        resp = await test_client.put(
            f"/api/auth/users/{user['id']}/active",
            headers=admin_headers,
            json={"is_active": True},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True


class TestAuditLog:
    async def test_query_audit_log(self, test_client, admin_headers, db_conn):
        resp = await test_client.get("/api/admin/audit-log", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data

    async def test_audit_log_non_admin(self, test_client, auth_headers, db_conn):
        resp = await test_client.get("/api/admin/audit-log", headers=auth_headers)
        assert resp.status_code == 403
