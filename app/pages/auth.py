from __future__ import annotations

import logging
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies import get_db
from app.services import auth as auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["pages"])


def _templates(request: Request):
    """Shortcut to the Jinja2 templates instance on app state."""
    return request.app.state.templates


def _ctx(request: Request, **kwargs) -> dict:
    """Build a template context dict with csrf_token always included."""
    ctx = {"request": request, "csrf_token": getattr(request.state, "csrf_token", "")}
    ctx.update(kwargs)
    return ctx


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    message: str | None = Query(None),
    error: str | None = Query(None),
    redirect_uri: str | None = Query(None),
):
    """Render the login page."""
    templates = _templates(request)
    return templates.TemplateResponse(
        "login.html",
        _ctx(request, message=message, error=error, redirect_uri=redirect_uri or ""),
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(""),
    redirect_uri: str = Form(""),
    conn=Depends(get_db),
):
    """Process the login form submission."""
    templates = _templates(request)
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip and request.client:
        ip = request.client.host
    ua = request.headers.get("user-agent", "")

    try:
        await auth_service.login_user(
            conn, email=email, password=password, ip_address=ip, user_agent=ua
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "login.html",
            _ctx(request, error=str(exc), email=email, redirect_uri=redirect_uri),
        )

    destination = redirect_uri if redirect_uri else "/"
    return RedirectResponse(url=destination, status_code=303)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render the registration page."""
    templates = _templates(request)
    return templates.TemplateResponse("register.html", _ctx(request))


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(""),
    conn=Depends(get_db),
):
    """Process the registration form submission."""
    templates = _templates(request)

    try:
        await auth_service.register_user(conn, email=email, password=password)
    except ValueError as exc:
        return templates.TemplateResponse(
            "register.html",
            _ctx(request, error=str(exc), email=email),
        )

    return RedirectResponse(
        url="/auth/login?message=" + quote_plus("Check your email to verify your account"),
        status_code=303,
    )


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Render the forgot-password page."""
    templates = _templates(request)
    return templates.TemplateResponse("forgot_password.html", _ctx(request))


@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_submit(
    request: Request,
    email: str = Form(...),
    csrf_token: str = Form(""),
    conn=Depends(get_db),
):
    """Process the forgot-password form. Always shows the same success message."""
    templates = _templates(request)

    try:
        await auth_service.forgot_password(conn, email=email)
    except Exception:
        # Suppress errors to prevent email enumeration.
        logger.debug("forgot_password page suppressed error for %s", email)

    return templates.TemplateResponse(
        "forgot_password.html",
        _ctx(request, success=True),
    )


# ---------------------------------------------------------------------------
# Reset Password
# ---------------------------------------------------------------------------


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(
    request: Request,
    token: str | None = Query(None),
):
    """Render the reset-password page. Requires a token query parameter."""
    templates = _templates(request)

    if not token:
        return templates.TemplateResponse(
            "reset_password.html",
            _ctx(request, token_error=True),
        )

    return templates.TemplateResponse(
        "reset_password.html",
        _ctx(request, token=token),
    )


@router.post("/reset-password", response_class=HTMLResponse)
async def reset_password_submit(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    csrf_token: str = Form(""),
    conn=Depends(get_db),
):
    """Process the reset-password form submission."""
    templates = _templates(request)

    try:
        await auth_service.reset_password(conn, token=token, new_password=new_password)
    except ValueError as exc:
        return templates.TemplateResponse(
            "reset_password.html",
            _ctx(request, error=str(exc), token=token),
        )

    return RedirectResponse(
        url="/auth/login?message=" + quote_plus("Password reset successful. You can now sign in."),
        status_code=303,
    )


# ---------------------------------------------------------------------------
# Verify Email
# ---------------------------------------------------------------------------


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(
    request: Request,
    token: str | None = Query(None),
    conn=Depends(get_db),
):
    """Auto-verify the email on page load and render the result."""
    templates = _templates(request)

    if not token:
        return templates.TemplateResponse(
            "verify_email.html",
            _ctx(request, error="Missing verification token."),
        )

    try:
        await auth_service.verify_email(conn, token=token)
    except ValueError as exc:
        return templates.TemplateResponse(
            "verify_email.html",
            _ctx(request, error=str(exc)),
        )

    return templates.TemplateResponse(
        "verify_email.html",
        _ctx(request, success=True),
    )
