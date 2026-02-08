"""AuthenticatedUser — represents logged-in users (80% of traffic)."""

import random
import uuid

from locust import HttpUser, between, task

from tests.load.helpers import (
    LOAD_TEST_PASSWORD,
    auth_header,
    forwarded_header,
    random_regular_email,
)


class AuthenticatedUser(HttpUser):
    """Simulates logged-in users performing typical auth operations."""

    weight = 80
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.email = random_regular_email()
        self.access_token = None
        self.refresh_token = None
        self._login()

    def _login(self):
        resp = self.client.post(
            "/api/auth/login",
            json={"email": self.email, "password": LOAD_TEST_PASSWORD},
            headers=forwarded_header(),
        )
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]

    def _auth_headers(self) -> dict:
        return auth_header(self.access_token) if self.access_token else {}

    @task(30)
    def get_me(self):
        if not self.access_token:
            return
        self.client.get("/api/auth/me", headers=self._auth_headers())

    @task(15)
    def refresh_token(self):
        if not self.refresh_token:
            return
        resp = self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": self.refresh_token},
        )
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
        else:
            # Token may have been revoked — fall back to full login
            self._login()

    @task(8)
    def list_sessions(self):
        if not self.access_token:
            return
        self.client.get("/api/auth/sessions", headers=self._auth_headers())

    @task(8)
    def login_again(self):
        self._login()

    @task(5)
    def update_profile(self):
        if not self.access_token:
            return
        self.client.put(
            "/api/auth/me",
            json={
                "display_name": f"LoadUser-{uuid.uuid4().hex[:8]}",
                "phone": f"+1555{random.randint(1000000, 9999999)}",
            },
            headers=self._auth_headers(),
        )

    @task(2)
    def change_password(self):
        if not self.access_token:
            return
        temp_password = f"TempPw_{uuid.uuid4().hex[:8]}!1"
        # Change to temporary password
        resp = self.client.put(
            "/api/auth/password",
            json={
                "current_password": LOAD_TEST_PASSWORD,
                "new_password": temp_password,
            },
            headers=self._auth_headers(),
            name="/api/auth/password [change]",
        )
        if resp.status_code != 200:
            return
        # Immediately change back to keep user valid for other tasks
        self.client.put(
            "/api/auth/password",
            json={
                "current_password": temp_password,
                "new_password": LOAD_TEST_PASSWORD,
            },
            headers=self._auth_headers(),
            name="/api/auth/password [restore]",
        )

    @task(2)
    def logout_single(self):
        if not self.refresh_token:
            return
        self.client.post(
            "/api/auth/logout",
            json={"refresh_token": self.refresh_token},
            headers=self._auth_headers(),
        )
        self.access_token = None
        self.refresh_token = None
        self._login()

    @task(1)
    def logout_all(self):
        if not self.access_token:
            return
        self.client.post(
            "/api/auth/logout-all",
            headers=self._auth_headers(),
        )
        self.access_token = None
        self.refresh_token = None
        self._login()

    @task(1)
    def health(self):
        self.client.get("/health")
