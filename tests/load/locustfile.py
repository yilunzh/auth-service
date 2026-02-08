"""Locust load testing scenarios for the auth service.

Three user personas with realistic traffic distribution:
  - AuthenticatedUser (80%) — logged-in users: profile, sessions, tokens
  - RegistrationUser  (15%) — new visitors: registration, forgot-password
  - AdminUser          (5%) — admins: user management, API keys, audit log

Pre-seed users before running:
    python -m tests.load.setup_users --count 1000 --admins 10 --flush-rate-limits

Usage:
    # Smoke test (10 users, 10s)
    locust -f tests/load/locustfile.py --headless --host http://localhost:8000 -u 10 -r 2 -t 10s

    # Medium load (100 users, 60s)
    locust -f tests/load/locustfile.py --headless --host http://localhost:8000 -u 100 -r 10 -t 60s

    # Full load (500 users, 5m)
    locust -f tests/load/locustfile.py --headless --host http://localhost:8000 -u 500 -r 50 -t 5m
"""

# Register event hooks
import tests.load.listeners  # noqa: F401
from tests.load.users import AdminUser, AuthenticatedUser, RegistrationUser

__all__ = ["AuthenticatedUser", "AdminUser", "RegistrationUser"]
