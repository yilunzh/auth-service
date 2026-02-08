"""Shared constants and utilities for load test user classes."""

import random

LOAD_TEST_PASSWORD = "LoadTest_Xk9m!z42"
NUM_REGULAR_USERS = 1000
NUM_ADMIN_USERS = 10


def random_regular_email() -> str:
    """Pick a random email from the pre-seeded regular user pool."""
    idx = random.randint(0, NUM_REGULAR_USERS - 1)
    return f"loadtest-{idx:05d}@test.com"


def random_admin_email() -> str:
    """Pick a random email from the pre-seeded admin user pool."""
    idx = random.randint(0, NUM_ADMIN_USERS - 1)
    return f"loadtest-admin-{idx:05d}@test.com"


def random_ip() -> str:
    """Generate a random private IP for X-Forwarded-For to distribute rate limit buckets."""
    return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def auth_header(token: str) -> dict:
    """Build Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


def forwarded_header() -> dict:
    """Build X-Forwarded-For header with a random private IP."""
    return {"X-Forwarded-For": random_ip()}
