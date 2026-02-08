from __future__ import annotations

import ipaddress
import logging

from fastapi import Depends, Header, HTTPException, Request

from app.config import settings
from app.db.pool import get_connection
from app.db.users import get_user_by_id
from app.services.token import decode_access_token

logger = logging.getLogger(__name__)


async def get_db():
    """Yield a database connection from the pool."""
    async with get_connection() as conn:
        yield conn


async def get_current_user(
    authorization: str = Header(None),
    conn=Depends(get_db),
) -> dict:
    """Extract and validate the current user from the Authorization header.

    Raises:
        HTTPException 401: If no valid Bearer token is provided, the token is
            invalid/expired, the user does not exist, or the user is inactive.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization[len("Bearer ") :]

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.get("is_active"):
        raise HTTPException(status_code=401, detail="Account is deactivated")

    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Ensure the current user has the admin role.

    Raises:
        HTTPException 403: If the user is not an admin.
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _is_trusted_proxy(addr: str, trusted: list[str]) -> bool:
    """Check if *addr* matches any entry in the trusted proxy list.

    Each entry can be an individual IP or a CIDR network (e.g. "10.0.0.0/8").
    """
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False

    for entry in trusted:
        try:
            if "/" in entry:
                if ip in ipaddress.ip_network(entry, strict=False):
                    return True
            else:
                if ip == ipaddress.ip_address(entry):
                    return True
        except ValueError:
            logger.warning("Invalid trusted proxy entry: %s", entry)
    return False


def resolve_client_ip(request: Request) -> str:
    """Determine the real client IP, respecting trusted proxy configuration.

    * No trusted proxies configured → always use ``request.client.host``
      (strictest default — ignore X-Forwarded-For entirely).
    * Request from a trusted proxy → use the first IP in X-Forwarded-For.
    * Request from an untrusted source → use ``request.client.host``.
    """
    direct_ip = request.client.host if request.client else "unknown"
    trusted = settings.trusted_proxies_list

    if not trusted:
        # No proxies configured — never trust forwarded headers
        return direct_ip

    if not _is_trusted_proxy(direct_ip, trusted):
        # Direct connection is NOT from a trusted proxy — ignore header
        return direct_ip

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return direct_ip


def get_client_ip(request: Request) -> str:
    """FastAPI dependency — return the resolved client IP."""
    return resolve_client_ip(request)


def get_user_agent(request: Request) -> str:
    """Return the User-Agent header value."""
    return request.headers.get("user-agent", "")
