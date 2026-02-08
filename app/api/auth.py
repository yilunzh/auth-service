from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.db import tokens as db_tokens
from app.db import users as db_users
from app.dependencies import get_client_ip, get_current_user, get_db, get_user_agent
from app.models.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.models.user import SessionResponse, UpdateProfileRequest, UserResponse
from app.services import auth as auth_service
from app.services import token as token_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(body: RegisterRequest, conn=Depends(get_db)):
    """Create a new user account and send a verification email."""
    try:
        await auth_service.register_user(conn, email=body.email, password=body.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return MessageResponse(message="Check your email to verify your account")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, conn=Depends(get_db)):
    """Authenticate a user and return access + refresh tokens."""
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    try:
        tokens = await auth_service.login_user(
            conn, email=body.email, password=body.password, ip_address=ip, user_agent=ua
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, conn=Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        access_token, refresh_token = await token_service.refresh_access_token(
            conn, body.refresh_token
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, conn=Depends(get_db)):
    """Request a password-reset email.

    Always returns the same response to prevent email enumeration.
    """
    try:
        await auth_service.forgot_password(conn, email=body.email)
    except Exception:
        # Swallow all errors — never reveal whether the email exists.
        logger.debug("forgot_password suppressed error for %s", body.email)
    return MessageResponse(message="If an account exists with that email, we sent a reset link.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, conn=Depends(get_db)):
    """Reset a user password using a valid reset token."""
    try:
        await auth_service.reset_password(conn, token=body.token, new_password=body.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return MessageResponse(message="Password reset successful. You can now sign in.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(body: VerifyEmailRequest, conn=Depends(get_db)):
    """Verify a user email address using the verification token."""
    try:
        await auth_service.verify_email(conn, token=body.token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return MessageResponse(message="Email verified successfully.")


# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """Return the current user profile."""
    return UserResponse(**user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Update the current user profile fields."""
    try:
        updated = await db_users.update_user_profile(
            conn,
            user_id=user["id"],
            display_name=body.display_name,
            phone=body.phone,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return UserResponse(**updated)


@router.put("/password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Change the current user password (requires old password)."""
    try:
        await auth_service.change_password(
            conn, user_id=user["id"], old_password=body.old_password, new_password=body.new_password
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return MessageResponse(message="Password changed successfully.")


@router.delete("/me", response_model=MessageResponse)
async def delete_me(
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Hard-delete the current user account (GDPR)."""
    try:
        await db_users.delete_user(conn, user_id=user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return MessageResponse(message="Account deleted successfully.")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: RefreshRequest,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Revoke the given refresh token (single-session logout)."""
    try:
        await token_service.revoke_token(conn, token=body.refresh_token, user_id=user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return MessageResponse(message="Logged out successfully.")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Revoke all refresh tokens for the current user (logout everywhere)."""
    await token_service.revoke_all_tokens(conn, user_id=user["id"])
    return MessageResponse(message="All sessions revoked.")


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """List active sessions (non-revoked refresh tokens) for the current user."""
    sessions = await db_tokens.list_user_sessions(conn, user_id=user["id"])
    return [SessionResponse(**s) for s in sessions]
