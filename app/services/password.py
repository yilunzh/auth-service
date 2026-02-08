"""Password hashing service using Argon2id.

Offloads CPU-intensive hashing to a dedicated thread pool so the async
event loop is never blocked.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

ph = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)

_hash_executor = ThreadPoolExecutor(max_workers=settings.PASSWORD_HASH_WORKERS)


async def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id.

    Runs in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_hash_executor, ph.hash, password)


async def verify_password(password: str, hash: str) -> bool:
    """Verify a plaintext password against an Argon2id hash.

    Returns True if the password matches, False otherwise.
    Runs in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(_hash_executor, ph.verify, hash, password)
    except VerifyMismatchError:
        return False
