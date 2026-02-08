"""Email sending service using async SMTP.

Provides helpers for sending verification and password-reset emails.
Connection errors are handled gracefully (logged but never crash the caller).
"""

import logging

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html_body: str) -> None:
    """Send an email via SMTP.

    Uses the SMTP settings from application configuration. Connection and
    delivery errors are logged but never raised to the caller so that
    upstream flows (registration, password reset) are not interrupted by
    transient mail failures.
    """
    try:
        await aiosmtplib.send(
            message=_build_message(to, subject, html_body),
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=True,
        )
    except Exception:
        logger.exception("Failed to send email to %s (subject: %s)", to, subject)


async def send_verification_email(to: str, token: str) -> None:
    """Send an email-verification link to the given address."""
    url = f"{settings.BASE_URL}/auth/verify-email?token={token}"
    subject = f"{settings.APP_NAME} - Verify your email"
    html_body = (
        f"<h2>Verify your email</h2>"
        f"<p>Click the link below to verify your email address:</p>"
        f'<p><a href="{url}">{url}</a></p>'
        f"<p>This link expires in 24 hours.</p>"
        f"<p>If you did not create an account, you can safely ignore this email.</p>"
    )
    await send_email(to, subject, html_body)


async def send_password_reset_email(to: str, token: str) -> None:
    """Send a password-reset link to the given address."""
    url = f"{settings.BASE_URL}/auth/reset-password?token={token}"
    subject = f"{settings.APP_NAME} - Reset your password"
    html_body = (
        f"<h2>Reset your password</h2>"
        f"<p>Click the link below to set a new password:</p>"
        f'<p><a href="{url}">{url}</a></p>'
        f"<p>This link expires in 1 hour.</p>"
        f"<p>If you did not request a password reset, you can safely ignore this email.</p>"
    )
    await send_email(to, subject, html_body)


def _build_message(to: str, subject: str, html_body: str) -> str:
    """Build a minimal MIME email message string."""
    from email.mime.text import MIMEText

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to
    return msg.as_string()
