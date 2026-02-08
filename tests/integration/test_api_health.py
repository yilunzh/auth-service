"""Integration tests for the health check endpoint."""


class TestHealth:
    async def test_health_check(self, test_client, db_conn):
        resp = await test_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "timestamp" in data

    async def test_health_response_fields(self, test_client, db_conn):
        resp = await test_client.get("/health")
        data = resp.json()
        expected_fields = {"status", "timestamp", "database"}
        assert expected_fields.issubset(set(data.keys()))
