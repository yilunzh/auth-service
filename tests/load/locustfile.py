"""Locust load testing scenarios for the auth service.

Pre-seeds users via setup_users.py, then simulates realistic auth traffic.

Usage:
    # Smoke test (10 users, 10s)
    locust -f tests/load/locustfile.py --headless --host http://localhost:8000 -u 10 -r 2 -t 10s

    # Full load test (200 users, 60s)
    locust -f tests/load/locustfile.py --headless --host http://localhost:8000 -u 200 -r 20 -t 60s
"""

import random

from locust import HttpUser, between, task

LOAD_TEST_PASSWORD = "LoadTest_Xk9m!z42"
NUM_USERS = 1000


class AuthUser(HttpUser):
    """Simulates an authenticated user performing typical auth operations."""

    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Login as a random pre-seeded user."""
        self.user_index = random.randint(0, NUM_USERS - 1)
        self.email = f"loadtest-{self.user_index:05d}@test.com"
        self.access_token = None
        self.refresh_token = None
        self._do_login()

    def _do_login(self):
        resp = self.client.post(
            "/api/auth/login",
            json={"email": self.email, "password": LOAD_TEST_PASSWORD},
        )
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]

    @task(10)
    def login(self):
        """Login flow — highest weight."""
        self._do_login()

    @task(3)
    def get_me(self):
        """Fetch user profile."""
        if not self.access_token:
            return
        self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

    @task(1)
    def health(self):
        """Health check."""
        self.client.get("/health")
