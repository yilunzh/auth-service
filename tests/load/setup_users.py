"""Bulk-create verified users in MySQL for load testing.

Usage:
    python -m tests.load.setup_users [--count 1000]
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
    """Create `count` verified users with known passwords."""
    conn = await aiomysql.connect(**DB_CONFIG, autocommit=True)
    pw_hash = ph.hash(LOAD_TEST_PASSWORD)
    now = datetime.utcnow()

    print(f"Creating {count} load test users...")

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
    print(f"Done. {count} users created with password: {LOAD_TEST_PASSWORD}")


def main():
    parser = argparse.ArgumentParser(description="Create load test users")
    parser.add_argument("--count", type=int, default=1000, help="Number of users to create")
    args = parser.parse_args()
    asyncio.run(create_users(args.count))


if __name__ == "__main__":
    main()
