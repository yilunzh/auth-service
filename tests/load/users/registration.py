"""RegistrationUser — represents new visitors registering or requesting password resets (15% of traffic)."""

import random
import uuid

from locust import HttpUser, between, task

from tests.load.helpers import LOAD_TEST_PASSWORD, forwarded_header, random_regular_email


class RegistrationUser(HttpUser):
    """Simulates new visitors who register or use forgot-password."""

    weight = 15
    wait_time = between(1.0, 5.0)

    @task(10)
    def register(self):
        email = f"loadreg-{uuid.uuid4().hex[:8]}@test.com"
        self.client.post(
            "/api/auth/register",
            json={"email": email, "password": LOAD_TEST_PASSWORD},
            headers=forwarded_header(),
        )

    @task(3)
    def forgot_password(self):
        # 50% real emails (triggers reset flow), 50% fake (silent failure path)
        if random.random() < 0.5:
            email = random_regular_email()
        else:
            email = f"nonexistent-{uuid.uuid4().hex[:8]}@test.com"
        self.client.post(
            "/api/auth/forgot-password",
            json={"email": email},
            headers=forwarded_header(),
        )

    @task(1)
    def health(self):
        self.client.get("/health")
