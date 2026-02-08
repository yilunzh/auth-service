"""Async MySQL connection pool using aiomysql.

Parses DATABASE_URL and manages a module-level connection pool with
async context manager access.
"""

from __future__ import annotations

import contextlib
from urllib.parse import urlparse

import aiomysql

_pool: aiomysql.Pool | None = None


def _parse_database_url(url: str) -> dict:
    """Parse a mysql:// URL into connection kwargs for aiomysql.

    Supports: mysql://user:pass@host:port/dbname
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("mysql", "mysql+aiomysql"):
        raise ValueError(f"Unsupported database scheme: {parsed.scheme!r}. Expected 'mysql'.")

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": parsed.username or "root",
        "password": parsed.password or "",
        "db": (parsed.path or "/").lstrip("/") or "auth_db",
    }


async def init_pool(settings) -> aiomysql.Pool:
    """Initialize the global connection pool from application settings.

    Args:
        settings: App config object with DATABASE_URL, DB_POOL_MIN, DB_POOL_MAX.

    Returns:
        The created aiomysql.Pool instance.
    """
    global _pool
    if _pool is not None:
        return _pool

    conn_kwargs = _parse_database_url(settings.DATABASE_URL)
    _pool = await aiomysql.create_pool(
        minsize=settings.DB_POOL_MIN,
        maxsize=settings.DB_POOL_MAX,
        autocommit=True,
        charset="utf8mb4",
        **conn_kwargs,
    )
    return _pool


async def close_pool() -> None:
    """Close the global connection pool and release all connections."""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


@contextlib.asynccontextmanager
async def get_connection():
    """Acquire a connection from the pool as an async context manager.

    Usage::

        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")

    Raises:
        RuntimeError: If the pool has not been initialized.
    """
    if _pool is None:
        raise RuntimeError(
            "Connection pool is not initialized. Call init_pool() during application startup."
        )
    async with _pool.acquire() as conn:
        yield conn
