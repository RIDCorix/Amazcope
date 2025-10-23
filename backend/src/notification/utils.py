"""Email notification utilities using Python's built-in smtplib.

This module provides simple email sending functionality without external dependencies.
Replaces fastapi-mail to avoid typing-extensions conflicts.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pydantic import BaseModel

from core.config import settings


class EmailSchema(BaseModel):
    """Email schema for sending notifications."""

    email: str
    subject: str
    body: str


async def send_email(to: str, subject: str, html: str) -> None:
    """Send email using SMTP.

    Args:
        to: Recipient email address
        subject: Email subject
        html: HTML body content

    Note:
        Uses Python's built-in smtplib instead of fastapi-mail
        to avoid typing-extensions dependency conflicts.
        This is a synchronous wrapper - email is sent immediately.
    """
    _send_email_sync(to, subject, html)


def _send_email_sync(to: str, subject: str, html_body: str) -> None:
    """Synchronous email sending function.

    This runs in a background task to avoid blocking the API.

    Args:
        to: Recipient email address
        subject: Email subject
        html_body: HTML body content
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
        msg["To"] = to

        # Add HTML body
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)

        # Connect and send
        if settings.MAIL_TLS:
            # Use STARTTLS (typically port 587)
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
                server.starttls()
                if settings.MAIL_USE_CREDENTIALS:
                    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD.get_secret_value())
                server.send_message(msg)
        elif settings.MAIL_SSL:
            # Use SSL/TLS (typically port 465)
            with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
                if settings.MAIL_USE_CREDENTIALS:
                    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD.get_secret_value())
                server.send_message(msg)
        else:
            # No encryption (not recommended for production)
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
                if settings.MAIL_USE_CREDENTIALS:
                    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD.get_secret_value())
                server.send_message(msg)

    except Exception as e:
        # Log error but don't crash the application
        from loguru import logger

        logger.error(f"Failed to send email to {to}: {e}")
