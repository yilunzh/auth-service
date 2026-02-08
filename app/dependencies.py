from fastapi import Depends, Header, HTTPException, Request

from app.db.pool import get_connection
from app.db.users import get_user_by_id
from app.services.token import decode_access_token


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

    token = authorization[len("Bearer "):]

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


def get_client_ip(request: Request) -> str:
    """Return the client IP address, respecting X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs; the first is the client.
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def get_user_agent(request: Request) -> str:
    """Return the User-Agent header value."""
    return request.headers.get("user-agent", "")
