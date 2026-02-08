"""Bulk-create verified users in MySQL for load testing.

Usage:
    python -m tests.load.setup_users [--count 1000] [--admins 10] [--flush-rate-limits] [--cleanup-registrations]
"""

import argparse
import asyncio
import uuid
from datetime import datetime

import aiomysql
from argon2 import PasswordHasher

LOAD_TEST_PASSWORD = "LoadTest_Xk9m!z42"
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "rootpassword",
    "db": "auth_db",
    "charset": "utf8mb4",
}

ph = PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


async def create_users(count: int):
    """Create `count` verified regular users with known passwords."""
    conn = await aiomysql.connect(**DB_CONFIG, autocommit=True)
    pw_hash = ph.hash(LOAD_TEST_PASSWORD)
    now = datetime.utcnow()

    print(f"Creating {count} regular load test users...")

    async with conn.cursor() as cur:
        for i in range(count):
            user_id = str(uuid.uuid4())
            email = f"loadtest-{i:05d}@test.com"
            await cur.execute(
                """INSERT IGNORE INTO users (id, email, password_hash, role, is_active, is_verified, created_at, updated_at)
                VALUES (%s, %s, %s, 'user', 1, 1, %s, %s)""",
                (user_id, email, pw_hash, now, now),
            )
            if (i + 1) % 100 == 0:
                print(f"  Created {i + 1}/{count}")

    conn.close()
    print(f"Done. {count} regular users created with password: {LOAD_TEST_PASSWORD}")


async def create_admin_users(count: int):
    """Create `count` verified admin users with known passwords."""
    conn = await aiomysql.connect(**DB_CONFIG, autocommit=True)
    pw_hash = ph.hash(LOAD_TEST_PASSWORD)
    now = datetime.utcnow()

    print(f"Creating {count} admin load test users...")

    async with conn.cursor() as cur:
        for i in range(count):
            user_id = str(uuid.uuid4())
            email = f"loadtest-admin-{i:05d}@test.com"
            await cur.execute(
                """INSERT IGNORE INTO users (id, email, password_hash, role, is_active, is_verified, created_at, updated_at)
                VALUES (%s, %s, %s, 'admin', 1, 1, %s, %s)""",
                (user_id, email, pw_hash, now, now),
            )

    conn.close()
    print(f"Done. {count} admin users created.")


async def flush_rate_limits():
    """Truncate the rate_limits table for a clean slate."""
    conn = await aiomysql.connect(**DB_CONFIG, autocommit=True)
    async with conn.cursor() as cur:
        await cur.execute("TRUNCATE TABLE rate_limits")
    conn.close()
    print("Rate limits table flushed.")


async def cleanup_registrations():
    """Delete users created by RegistrationUser during previous load test runs."""
    conn = await aiomysql.connect(**DB_CONFIG, autocommit=True)
    async with conn.cursor() as cur:
        await cur.execute("DELETE FROM users WHERE email LIKE 'loadreg-%%@test.com'")
        deleted = cur.rowcount
    conn.close()
    print(f"Cleaned up {deleted} registration test users.")


async def run(args):
    await create_users(args.count)
    if args.admins > 0:
        await create_admin_users(args.admins)
    if args.flush_rate_limits:
        await flush_rate_limits()
    if args.cleanup_registrations:
        await cleanup_registrations()


def main():
    parser = argparse.ArgumentParser(description="Create load test users")
    parser.add_argument("--count", type=int, default=1000, help="Number of regular users to create")
    parser.add_argument("--admins", type=int, default=10, help="Number of admin users to create")
    parser.add_argument(
        "--flush-rate-limits", action="store_true", help="Truncate rate_limits table"
    )
    parser.add_argument(
        "--cleanup-registrations",
        action="store_true",
        help="Delete loadreg-* users from previous runs",
    )
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
