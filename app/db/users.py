"""Database layer for user operations.

All functions are async, take a connection (conn) as the first parameter,
and use parameterized queries with %s placeholders.
"""

from __future__ import annotations

import json
from datetime import datetime

import aiomysql


async def create_user(conn, id: str, email: str, password_hash: str, role: str = "user") -> dict:
    """Create a new user and return the user dict."""
    now = datetime.utcnow()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """
            INSERT INTO users (id, email, password_hash, role, is_active, is_verified, created_at, updated_at)
            VALUES (%s, %s, %s, %s, 1, 0, %s, %s)
            """,
            (id, email, password_hash, role, now, now),
        )
        await conn.commit()
    return {
        "id": id,
        "email": email,
        "role": role,
        "is_active": True,
        "is_verified": False,
        "display_name": None,
        "phone": None,
        "metadata": None,
        "created_at": now,
        "updated_at": now,
    }


async def get_user_by_email(conn, email: str) -> dict | None:
    """Look up a user by email. Returns None if not found."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = await cur.fetchone()
    if row is None:
        return None
    return _normalize_user_row(row)


async def get_user_by_id(conn, user_id: str) -> dict | None:
    """Look up a user by ID. Returns None if not found."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = await cur.fetchone()
    if row is None:
        return None
    return _normalize_user_row(row)


async def update_user_profile(
    conn,
    user_id: str,
    display_name: str | None = None,
    phone: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """Update user profile fields. Only non-None arguments are updated.

    Returns the updated user dict.
    """
    sets: list[str] = []
    params: list = []

    if display_name is not None:
        sets.append("display_name = %s")
        params.append(display_name)
    if phone is not None:
        sets.append("phone = %s")
        params.append(phone)
    if metadata is not None:
        sets.append("metadata = %s")
        params.append(json.dumps(metadata))

    if not sets:
        # Nothing to update - return current state.
        return await get_user_by_id(conn, user_id)  # type: ignore[return-value]

    params.append(user_id)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            f"UPDATE users SET {', '.join(sets)} WHERE id = %s",  # nosec B608
            tuple(params),
        )
        await conn.commit()

    return await get_user_by_id(conn, user_id)  # type: ignore[return-value]


async def update_user_password(conn, user_id: str, password_hash: str) -> None:
    """Update a user's password hash."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, user_id),
        )
        await conn.commit()


async def update_user_role(conn, user_id: str, role: str) -> None:
    """Update a user's role (e.g. 'user' or 'admin')."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "UPDATE users SET role = %s WHERE id = %s",
            (role, user_id),
        )
        await conn.commit()


async def update_user_active(conn, user_id: str, is_active: bool) -> None:
    """Activate or deactivate a user."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "UPDATE users SET is_active = %s WHERE id = %s",
            (int(is_active), user_id),
        )
        await conn.commit()


async def set_user_verified(conn, user_id: str) -> None:
    """Mark a user's email as verified."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "UPDATE users SET is_verified = 1 WHERE id = %s",
            (user_id,),
        )
        await conn.commit()


async def delete_user(conn, user_id: str) -> None:
    """Hard-delete a user. CASCADE foreign keys handle related token rows."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        await conn.commit()


async def list_users(conn, page: int = 1, per_page: int = 20) -> tuple[list, int]:
    """Return a paginated list of users and the total count.

    Returns:
        (users, total_count)
    """
    offset = (page - 1) * per_page

    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT COUNT(*) AS cnt FROM users")
        total = (await cur.fetchone())["cnt"]

        await cur.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (per_page, offset),
        )
        rows = await cur.fetchall()

    return [_normalize_user_row(r) for r in rows], total


def _normalize_user_row(row: dict) -> dict:
    """Normalize a raw DB row into a consistent user dict.

    Converts tinyint booleans and deserializes JSON metadata.
    """
    row = dict(row)
    row["is_active"] = bool(row.get("is_active"))
    row["is_verified"] = bool(row.get("is_verified"))
    if isinstance(row.get("metadata"), str):
        try:
            row["metadata"] = json.loads(row["metadata"])
        except (json.JSONDecodeError, TypeError):
            pass
    return row
