"""
Email utilities for sending verification and password reset emails.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import settings
from utils.logging import get_logger

logger = get_logger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str | None = None,
) -> bool:
    """
    Send an email using SMTP.

    In development, this logs the email instead of sending.
    In production, configure SMTP settings in environment variables.
    """
    # Development mode - just log the email
    if settings.app_env == "development":
        logger.info(
            "Email (dev mode - not sent)",
            extra={
                "to": to_email,
                "subject": subject,
                "content": html_content,
            },
        )
        return True

    # Production mode - send actual email
    try:
        # Check if SMTP is configured
        if not all(
            [settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password]
        ):
            logger.warning("SMTP not configured, email not sent", extra={"to": to_email})
            return False

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email
        msg["To"] = to_email

        # Add text and HTML parts
        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        # Send email
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info("Email sent successfully", extra={"to": to_email, "subject": subject})
        return True

    except Exception as e:
        logger.error("Failed to send email", extra={"to": to_email, "error": str(e)}, exc_info=True)
        return False


async def send_verification_email(email: str, token: str, base_url: str) -> bool:
    """Send email verification link."""
    verification_link = f"{base_url}/api/v1/auth/verify-email?token={token}"

    subject = "Verify Your Email - Job Copilot"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Welcome to Job Copilot!</h2>
            <p>Thank you for registering. Please verify your email address to get started.</p>
            <p>
                <a href="{verification_link}" class="button">Verify Email</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{verification_link}</p>
            <p>This link will expire in 24 hours.</p>
            <div class="footer">
                <p>If you didn't create an account, please ignore this email.</p>
                <p>&copy; 2025 Job Copilot. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Welcome to Job Copilot!

    Thank you for registering. Please verify your email address by clicking the link below:

    {verification_link}

    This link will expire in 24 hours.

    If you didn't create an account, please ignore this email.
    """

    return await send_email(email, subject, html_content, text_content)


async def send_password_reset_email(email: str, token: str, base_url: str) -> bool:
    """Send password reset link."""
    reset_link = f"{base_url}/reset-password?token={token}"

    subject = "Reset Your Password - Job Copilot"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #2196F3;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 12px;
                margin: 20px 0;
            }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password for your Job Copilot account.</p>
            <p>
                <a href="{reset_link}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{reset_link}</p>
            <div class="warning">
                <strong>Security Notice:</strong> This link will expire in 1 hour for your security.
            </div>
            <div class="footer">
                <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
                <p>&copy; 2025 Job Copilot. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Password Reset Request

    We received a request to reset your password for your Job Copilot account.

    Click the link below to reset your password:
    {reset_link}

    This link will expire in 1 hour for your security.

    If you didn't request a password reset, please ignore this email.
    """

    return await send_email(email, subject, html_content, text_content)
