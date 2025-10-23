"""Notification topics system for structured messaging.

This module provides a simple, type-safe way to send notifications
through multiple channels (in-app notifications and email) with
HTML template support.

Usage:
    from notifications.topics import daily_report_topic

    await daily_report_topic.send(
        user_id=user_id,
        product_id=product_id,
        message="Amazcope analysis complete",
        suggestions=[...],
        summary_message="Your products are performing well"
    )
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

import jinja2
from pydantic import BaseModel
from sqlalchemy import select

from core.database import get_async_db_context
from notification.models import Notification
from notification.utils import send_email
from users.models import User, UserSettings

# Type variable for topic data models
T = TypeVar("T", bound=BaseModel)

# Base template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class NotificationTopic(Generic[T]):
    """A notification topic that can send messages through multiple channels.

    Each topic represents a specific type of notification (e.g., daily report,
    price alert, etc.) and can send both in-app notifications and emails
    using HTML templates.
    """

    def __init__(
        self,
        email_template_path: str,
        notification_type: str = "system",
        default_priority: str = "normal",
    ):
        """Initialize notification topic.

        Args:
            email_template_path: Path to HTML template relative to templates/ directory
            notification_type: Type for database notification categorization
            default_priority: Default priority level (low, normal, high, urgent)
        """
        self.email_template_path = email_template_path
        self.notification_type = notification_type
        self.default_priority = default_priority

        # Initialize Jinja2 environment for HTML templates
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )

    async def send(
        self,
        user_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        title: str | None = None,
        message: str | None = None,
        priority: str | None = None,
        action_url: str | None = None,
        email_subject: str | None = None,
        **template_data: Any,
    ) -> dict[str, Any]:
        """Send notification through all applicable channels.

        Args:
            user_id: Target user ID (if None, sends to all users with enabled settings)
            product_id: Related product ID (optional)
            title: Notification title
            message: Notification message
            priority: Priority level override
            action_url: Action button URL
            email_subject: Email subject line
            **template_data: Additional data for template rendering

        Returns:
            dict: Results with counts of notifications sent and any errors
        """
        results: dict[str, Any] = {"notifications_created": 0, "emails_sent": 0, "errors": []}

        # Determine target users
        target_users = await self._get_target_users(user_id)

        if not target_users:
            results["errors"].append("No target users found")
            return results

        # Render email template
        email_html = None
        if self.email_template_path:
            try:
                template = self.jinja_env.get_template(self.email_template_path)

                # Add common template variables
                template_context = {
                    "report_date": datetime.utcnow().strftime("%B %d, %Y"),
                    "dashboard_url": "https://app.amazcope.com/dashboard",
                    "settings_url": "https://app.amazcope.com/settings",
                    "unsubscribe_url": "https://app.amazcope.com/unsubscribe",
                    **template_data,
                }

                email_html = template.render(**template_context)
            except Exception as e:
                results["errors"].append(f"Template rendering failed: {str(e)}")
                return results

        # Send to each target user
        for user, settings in target_users:
            try:
                # Create in-app notification
                notification_data = await self._create_notification(
                    user_id=user.id,
                    product_id=product_id,
                    title=title or f"Daily Report - {datetime.utcnow().strftime('%B %d')}",
                    message=message or "Your daily product analysis is ready",
                    priority=priority or self.default_priority,
                    action_url=action_url,
                    template_data=template_data,
                )

                if notification_data:
                    results["notifications_created"] += 1

                # Send email if enabled and template available
                if (
                    email_html
                    and settings
                    and settings.email_notifications_enabled
                    and settings.daily_summary_emails
                ):
                    email_success = await self._send_email(
                        user=user,
                        subject=email_subject
                        or f"Daily Report - {datetime.utcnow().strftime('%B %d, %Y')}",
                        html_content=email_html,
                    )

                    if email_success:
                        results["emails_sent"] += 1

                        # Update notification record with email status
                        if notification_data:
                            await self._update_email_status(notification_data["id"], True)
                    else:
                        if notification_data:
                            await self._update_email_status(
                                notification_data["id"], False, "Failed to send email"
                            )

            except Exception as e:
                results["errors"].append(f"Failed to send to user {user.id}: {str(e)}")
                continue

        return results

    async def _get_target_users(
        self, user_id: uuid.UUID | None = None
    ) -> list[tuple[User, UserSettings | None]]:
        """Get target users for notification.

        Args:
            user_id: Specific user ID, or None for all active users

        Returns:
            List of (User, UserSettings) tuples
        """
        async with get_async_db_context() as db:
            if user_id:
                # Send to specific user
                user_result = await db.execute(
                    select(User).where(User.id == user_id, User.is_active)
                )
                user = user_result.scalar_one_or_none()

                if user:
                    settings_result = await db.execute(
                        select(UserSettings).where(UserSettings.user_id == user.id)
                    )
                    settings = settings_result.scalar_one_or_none()
                    return [(user, settings)]
                return []
            else:
                # Send to all active users with daily summary emails enabled
                result = await db.execute(
                    select(User, UserSettings)
                    .join(UserSettings, User.id == UserSettings.user_id, isouter=True)
                    .where(User.is_active, User.is_verified)
                )
                return [(user, settings) for user, settings in result.all()]

    async def _create_notification(
        self,
        user_id: uuid.UUID,
        product_id: uuid.UUID | None,
        title: str,
        message: str,
        priority: str,
        action_url: str | None,
        template_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Create in-app notification record.

        Returns:
            dict: Notification data with ID, or None if failed
        """
        async with get_async_db_context() as db:
            notification = Notification(
                user_id=user_id,
                product_id=product_id,
                title=title,
                message=message,
                data=template_data,
                priority=priority,
                action_url=action_url,
                notification_type=self.notification_type,
            )

            db.add(notification)
            await db.commit()
            await db.refresh(notification)

            return {
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "created_at": notification.created_at,
            }

    async def _send_email(self, user: User, subject: str, html_content: str) -> bool:
        """Send email to user.

        Returns:
            bool: True if email was sent successfully
        """
        try:
            # Send email directly (synchronous SMTP)
            await send_email(to=user.email, subject=subject, html=html_content)
            return True
        except Exception as e:
            from loguru import logger

            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            return False

    async def _update_email_status(
        self,
        notification_id: uuid.UUID,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        """Update notification with email sending status."""
        try:
            async with get_async_db_context() as db:
                result = await db.execute(
                    select(Notification).where(Notification.id == notification_id)
                )
                notification = result.scalar_one_or_none()

                if notification:
                    notification.email_sent = success
                    notification.email_sent_at = datetime.utcnow() if success else None
                    notification.email_error = error_message

                    await db.commit()
        except Exception as e:
            from loguru import logger

            logger.error(f"Failed to update email status: {str(e)}")


# Daily Report Topic Data Model
class DailyReportData(BaseModel):
    """Data structure for daily report notifications."""

    products_analyzed: int = 0
    suggestions_created: int = 0
    critical_issues: int = 0
    opportunities: int = 0
    summary_message: str | None = None
    suggestions: list[dict[str, Any]] = []
    market_insights: str | None = None
    action_items: list[str] = []


# Pre-configured notification topics
daily_report_topic: NotificationTopic[DailyReportData] = NotificationTopic(
    email_template_path="daily-report.html",
    notification_type="daily_report",
    default_priority="normal",
)
