"""AdminUser — represents admin users managing users and API keys (5% of traffic)."""

import random

from locust import HttpUser, between, task

from tests.load.helpers import (
    LOAD_TEST_PASSWORD,
    auth_header,
    forwarded_header,
    random_admin_email,
)


class AdminUser(HttpUser):
    """Simulates admin users performing management operations."""

    weight = 5
    wait_time = between(1.0, 3.0)

    def on_start(self):
        self.email = random_admin_email()
        self.access_token = None
        self.cached_user_ids: list[str] = []
        self.cached_key_ids: list[str] = []
        self._login()

    def _login(self):
        resp = self.client.post(
            "/api/auth/login",
            json={"email": self.email, "password": LOAD_TEST_PASSWORD},
            headers=forwarded_header(),
            name="/api/auth/login [admin]",
        )
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data["access_token"]

    def _auth_headers(self) -> dict:
        return auth_header(self.access_token) if self.access_token else {}

    @task(10)
    def list_users(self):
        if not self.access_token:
            return
        resp = self.client.get(
            "/api/auth/users",
            params={"page": 1, "page_size": 20},
            headers=self._auth_headers(),
        )
        if resp.status_code == 200:
            users = resp.json().get("data", [])
            self.cached_user_ids = [u["id"] for u in users]

    @task(8)
    def get_audit_log(self):
        if not self.access_token:
            return
        self.client.get(
            "/api/admin/audit-log",
            params={"page": 1, "page_size": 20},
            headers=self._auth_headers(),
        )

    @task(5)
    def list_api_keys(self):
        if not self.access_token:
            return
        resp = self.client.get("/api/keys/", headers=self._auth_headers())
        if resp.status_code == 200:
            keys = resp.json().get("data", [])
            self.cached_key_ids = [k["id"] for k in keys if k.get("revoked_at") is None]

    @task(3)
    def create_api_key(self):
        if not self.access_token:
            return
        resp = self.client.post(
            "/api/keys/",
            json={"name": f"loadtest-key-{random.randint(0, 99999):05d}"},
            headers=self._auth_headers(),
        )
        if resp.status_code == 201:
            key_id = resp.json().get("id")
            if key_id:
                self.cached_key_ids.append(key_id)

    @task(3)
    def get_api_key_detail(self):
        if not self.access_token or not self.cached_key_ids:
            return
        key_id = random.choice(self.cached_key_ids)
        self.client.get(
            f"/api/keys/{key_id}",
            headers=self._auth_headers(),
            name="/api/keys/[id]",
        )

    @task(2)
    def rotate_api_key(self):
        if not self.access_token or not self.cached_key_ids:
            return
        key_id = random.choice(self.cached_key_ids)
        self.client.post(
            f"/api/keys/{key_id}/rotate",
            headers=self._auth_headers(),
            name="/api/keys/[id]/rotate",
        )

    @task(1)
    def revoke_api_key(self):
        if not self.access_token or not self.cached_key_ids:
            return
        key_id = self.cached_key_ids.pop()
        self.client.delete(
            f"/api/keys/{key_id}",
            headers=self._auth_headers(),
            name="/api/keys/[id]",
        )

    @task(1)
    def change_user_role(self):
        if not self.access_token or not self.cached_user_ids:
            return
        user_id = random.choice(self.cached_user_ids)
        # Promote to admin, then immediately demote back
        self.client.put(
            f"/api/auth/users/{user_id}/role",
            json={"role": "admin"},
            headers=self._auth_headers(),
            name="/api/auth/users/[id]/role [promote]",
        )
        self.client.put(
            f"/api/auth/users/{user_id}/role",
            json={"role": "user"},
            headers=self._auth_headers(),
            name="/api/auth/users/[id]/role [demote]",
        )

    @task(1)
    def toggle_user_active(self):
        if not self.access_token or not self.cached_user_ids:
            return
        user_id = random.choice(self.cached_user_ids)
        # Deactivate, then immediately reactivate
        self.client.put(
            f"/api/auth/users/{user_id}/active",
            json={"is_active": False},
            headers=self._auth_headers(),
            name="/api/auth/users/[id]/active [deactivate]",
        )
        self.client.put(
            f"/api/auth/users/{user_id}/active",
            json={"is_active": True},
            headers=self._auth_headers(),
            name="/api/auth/users/[id]/active [reactivate]",
        )
