"""
CSRF protection middleware for hosted auth pages.

Implements the double-submit cookie pattern:
- On GET requests to /auth/*: generates a CSRF token, sets it as a cookie,
  and makes it available for template rendering via request.state.csrf_token.
- On POST requests to /auth/*: validates the csrf_token form field against
  the csrf cookie. Returns 403 on mismatch.
"""

import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

CSRF_COOKIE_NAME = "csrf_token"
CSRF_TOKEN_LENGTH = 32


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection for hosted page routes (/auth/*)."""

    def __init__(self, app, secure_cookies: bool = False):
        super().__init__(app)
        self.secure_cookies = secure_cookies

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Only apply to hosted auth page routes
        if not path.startswith("/auth/"):
            return await call_next(request)

        if request.method == "GET":
            return await self._handle_get(request, call_next)
        elif request.method == "POST":
            return await self._handle_post(request, call_next)
        else:
            return await call_next(request)

    async def _handle_get(self, request: Request, call_next) -> Response:
        """Ensure a CSRF cookie exists and pass the token to templates."""
        csrf_token = request.cookies.get(CSRF_COOKIE_NAME)

        if not csrf_token:
            csrf_token = secrets.token_urlsafe(CSRF_TOKEN_LENGTH)

        # Make token available for template rendering
        request.state.csrf_token = csrf_token

        response = await call_next(request)

        # Always set the cookie to ensure it's fresh
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            samesite="strict",
            httponly=False,  # JS needs to read this for the meta tag
            secure=self.secure_cookies,
            path="/auth/",
            max_age=3600,  # 1 hour
        )

        return response

    async def _handle_post(self, request: Request, call_next) -> Response:
        """Validate the CSRF token from form data against the cookie."""
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)

        if not cookie_token:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed: missing cookie"},
            )

        # Read CSRF token from form data
        try:
            form = await request.form()
            form_token = form.get("csrf_token", "")
        except Exception:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed: unable to read form"},
            )

        # Constant-time comparison
        if not secrets.compare_digest(str(cookie_token), str(form_token)):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed: token mismatch"},
            )

        # Token is valid — pass it through for template re-rendering on errors
        request.state.csrf_token = cookie_token

        return await call_next(request)
