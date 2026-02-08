"""Integration tests for API key management endpoints."""


class TestCreateKey:
    async def test_create_api_key(self, test_client, admin_headers, db_conn):
        resp = await test_client.post(
            "/api/keys/",
            headers=admin_headers,
            json={"name": "test-key"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["key"].startswith("ask_live_")
        assert data["name"] == "test-key"

    async def test_create_key_non_admin(self, test_client, auth_headers, db_conn):
        resp = await test_client.post(
            "/api/keys/",
            headers=auth_headers,
            json={"name": "test-key"},
        )
        assert resp.status_code == 403

    async def test_create_key_unauthenticated(self, test_client, db_conn):
        resp = await test_client.post(
            "/api/keys/",
            json={"name": "test-key"},
        )
        assert resp.status_code == 401


class TestListKeys:
    async def test_list_keys(self, test_client, admin_headers, db_conn):
        # Create a key first
        await test_client.post(
            "/api/keys/",
            headers=admin_headers,
            json={"name": "list-test-key"},
        )

        resp = await test_client.get("/api/keys/", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert len(data["data"]) >= 1
        # Verify no full key is exposed
        for key in data["data"]:
            assert "key" not in key or not key.get("key", "").startswith("ask_live_")


class TestGetKey:
    async def test_get_key_by_id(self, test_client, admin_headers, db_conn):
        create_resp = await test_client.post(
            "/api/keys/",
            headers=admin_headers,
            json={"name": "get-test-key"},
        )
        key_id = create_resp.json()["id"]

        resp = await test_client.get(f"/api/keys/{key_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == key_id


class TestRotateKey:
    async def test_rotate_key(self, test_client, admin_headers, db_conn):
        create_resp = await test_client.post(
            "/api/keys/",
            headers=admin_headers,
            json={"name": "rotate-test-key"},
        )
        key_id = create_resp.json()["id"]

        resp = await test_client.post(
            f"/api/keys/{key_id}/rotate",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"].startswith("ask_live_")
        assert data["id"] != key_id  # New key has a different ID


class TestRevokeKey:
    async def test_revoke_key(self, test_client, admin_headers, db_conn):
        create_resp = await test_client.post(
            "/api/keys/",
            headers=admin_headers,
            json={"name": "revoke-test-key"},
        )
        key_id = create_resp.json()["id"]

        resp = await test_client.delete(f"/api/keys/{key_id}", headers=admin_headers)
        assert resp.status_code == 200
