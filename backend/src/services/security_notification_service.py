"""Email notification service for security alerts.

Handles sending email notifications for:
- Suspicious login attempts
- Account lockouts
- Password changes
- Email verification
"""

from datetime import datetime
from typing import Any

from loguru import logger

from core.config import settings
from notification.utils import send_email


class SecurityNotificationService:
    """Service for sending security-related email notifications."""

    @staticmethod
    async def send_suspicious_login_alert(
        user_email: str,
        username: str,
        ip_address: str,
        timestamp: datetime,
        details: dict[str, Any] | None = None,
    ) -> bool:
        """Send email alert for suspicious login attempt.

        Args:
            user_email: User's email address
            username: Username
            ip_address: IP address of login attempt
            timestamp: Timestamp of login attempt
            details: Additional details (device, location, etc.)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = f"⚠️ Suspicious Login Attempt Detected - {settings.APP_NAME}"

            location = (
                details.get("location", "Unknown location") if details else "Unknown location"
            )
            device = details.get("device", "Unknown device") if details else "Unknown device"

            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #d32f2f;">⚠️ Suspicious Login Attempt Detected</h2>

                    <p>Hello <strong>{username}</strong>,</p>

                    <p>We detected a suspicious login attempt on your account:</p>

                    <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #d32f2f; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Time:</strong> {timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                        <p style="margin: 5px 0;"><strong>IP Address:</strong> {ip_address}</p>
                        <p style="margin: 5px 0;"><strong>Location:</strong> {location}</p>
                        <p style="margin: 5px 0;"><strong>Device:</strong> {device}</p>
                    </div>

                    <p><strong>If this was you:</strong></p>
                    <ul>
                        <li>No action is required</li>
                        <li>Your account is secure</li>
                    </ul>

                    <p><strong>If this wasn't you:</strong></p>
                    <ul>
                        <li>Change your password immediately</li>
                        <li>Enable two-factor authentication</li>
                        <li>Review your recent account activity</li>
                    </ul>

                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
                        This is an automated security notification from {settings.APP_NAME}.<br>
                        If you need assistance, please contact our support team.
                    </p>
                </div>
            </body>
            </html>
            """

            await send_email(to=user_email, subject=subject, html=body)

            return True

        except Exception as e:
            logger.error(f"Failed to send suspicious login alert: {str(e)}")
            return False

    @staticmethod
    async def send_account_lockout_notification(
        user_email: str,
        username: str,
        lockout_duration_minutes: int,
        failed_attempts: int,
    ) -> bool:
        """Send email notification when account is locked.

        Args:
            user_email: User's email address
            username: Username
            lockout_duration_minutes: Duration of lockout in minutes
            failed_attempts: Number of failed attempts

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = (
                f"🔒 Account Locked Due to Multiple Failed Login Attempts - {settings.APP_NAME}"
            )

            # Create email body with account lockout information
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #f57c00;">🔒 Account Temporarily Locked</h2>

                    <p>Hello <strong>{username}</strong>,</p>

                    <p>Your account has been temporarily locked due to multiple failed login attempts.</p>

                    <div style="background-color: #fff3e0; padding: 15px; border-left: 4px solid #f57c00; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Failed Attempts:</strong> {failed_attempts}</p>
                        <p style="margin: 5px 0;"><strong>Lockout Duration:</strong> {lockout_duration_minutes} minutes</p>
                        <p style="margin: 5px 0;"><strong>Time:</strong> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                    </div>

                    <p><strong>What this means:</strong></p>
                    <ul>
                        <li>Your account is temporarily locked for security</li>
                        <li>You can try logging in again after {lockout_duration_minutes} minutes</li>
                        <li>The lockout will automatically expire</li>
                    </ul>

                    <p><strong>Security recommendations:</strong></p>
                    <ul>
                        <li>Ensure you're using the correct password</li>
                        <li>Check for typos in your email/username</li>
                        <li>If you've forgotten your password, use the "Forgot Password" link</li>
                        <li>If you didn't make these login attempts, change your password immediately</li>
                    </ul>

                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
                        This is an automated security notification from {settings.APP_NAME}.<br>
                        If you need assistance, please contact our support team.
                    </p>
                </div>
            </body>
            </html>
            """

            logger.warning(
                f"ACCOUNT LOCKOUT: {username} locked for {lockout_duration_minutes} minutes after {failed_attempts} failed attempts"
            )
            logger.info(f"Lockout notification sent to {user_email}")

            # TODO: Integrate with actual email service
            await send_email(to=user_email, subject=subject, html=body)

            return True

        except Exception as e:
            logger.error(f"Failed to send account lockout notification: {str(e)}")
            return False

    @staticmethod
    async def send_successful_login_from_new_location(
        user_email: str,
        username: str,
        ip_address: str,
        location: str,
        device: str,
    ) -> bool:
        """Send notification for login from new location.

        Args:
            user_email: User's email address
            username: Username
            ip_address: IP address of login
            location: Approximate location
            device: Device information

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = f"📍 New Login Location Detected - {settings.APP_NAME}"

            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #1976d2;">📍 New Login Location Detected</h2>

                    <p>Hello <strong>{username}</strong>,</p>

                    <p>We noticed a successful login to your account from a new location:</p>

                    <div style="background-color: #e3f2fd; padding: 15px; border-left: 4px solid #1976d2; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Time:</strong> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                        <p style="margin: 5px 0;"><strong>IP Address:</strong> {ip_address}</p>
                        <p style="margin: 5px 0;"><strong>Location:</strong> {location}</p>
                        <p style="margin: 5px 0;"><strong>Device:</strong> {device}</p>
                    </div>

                    <p><strong>If this was you:</strong></p>
                    <ul>
                        <li>No action is required</li>
                        <li>Your account is secure</li>
                    </ul>

                    <p><strong>If this wasn't you:</strong></p>
                    <ul>
                        <li>Change your password immediately</li>
                        <li>Review your recent account activity</li>
                        <li>Enable two-factor authentication for added security</li>
                    </ul>

                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
                        This is an automated security notification from {settings.APP_NAME}.<br>
                        If you need assistance, please contact our support team.
                    </p>
                </div>
            </body>
            </html>
            """

            logger.info(f"New location login: {username} from {ip_address} ({location})")
            logger.info(f"New location notification sent to {user_email}")

            # TODO: Integrate with actual email service
            await send_email(to=user_email, subject=subject, html=body)

            return True

        except Exception as e:
            logger.error(f"Failed to send new location notification: {str(e)}")
            return False
