"""Notification service for creating and sending notifications."""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from notification.models import Notification
from products.models import Product
from users.models import User, UserSettings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""

    NOTIFICATION_TYPES = {
        "price_change": "Price Change Alert",
        "bsr_change": "BSR Change Alert",
        "stock_change": "Stock Status Alert",
        "review_change": "Review Change Alert",
        "system": "System Notification",
        "daily_summary": "Daily Summary",
        "weekly_report": "Weekly Report",
    }

    @classmethod
    async def create_price_change_notification(
        cls,
        db: AsyncSession,
        user: User,
        product: Product,
        old_price: float,
        new_price: float,
        threshold: float,
    ) -> Notification | None:
        """Create a price change notification.

        Args:
            user: User to notify
            product: Product that changed
            old_price: Previous price
            new_price: Current price
            threshold: Threshold percentage

        Returns:
            Notification instance or None if user has disabled this notification type
        """
        # Check user settings
        stmt = select(UserSettings).where(UserSettings.user_id == user.id)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        # Create default settings if not exists
        if not settings:
            settings = UserSettings(user_id=user.id)
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

        if not settings.email_notifications_enabled or not settings.price_alert_emails:
            return None

        # Calculate percentage change
        price_change = ((new_price - old_price) / old_price) * 100
        change_direction = "increased" if new_price > old_price else "decreased"

        title = f"Price Alert: {product.title[:50]}..."
        message = (
            f"The price of {product.title} has {change_direction} by {abs(price_change):.1f}%.\n\n"
            f"Previous price: ${old_price:.2f}\n"
            f"Current price: ${new_price:.2f}\n"
            f"Change: ${abs(new_price - old_price):.2f}"
        )

        notification = Notification(
            user_id=user.id,
            notification_type="price_change",
            title=title,
            message=message,
            product_id=product.id,
            data={
                "old_price": old_price,
                "new_price": new_price,
                "change_percentage": price_change,
                "threshold": threshold,
            },
            priority="high" if abs(price_change) > threshold * 2 else "normal",
            action_url=f"/products/{product.id}",
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # TODO: Queue email sending task
        # await email_service.send_notification_email(user, notification)

        return notification

    @classmethod
    async def create_bsr_change_notification(
        cls,
        db: AsyncSession,
        user: User,
        product: Product,
        old_bsr: int,
        new_bsr: int,
        threshold: float,
    ) -> Notification | None:
        """Create a BSR change notification."""
        stmt = select(UserSettings).where(UserSettings.user_id == user.id)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings:
            settings = UserSettings(user_id=user.id)
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

        if not settings.email_notifications_enabled or not settings.bsr_alert_emails:
            return None

        # Calculate percentage change (lower BSR is better)
        bsr_change = ((new_bsr - old_bsr) / old_bsr) * 100
        change_direction = "improved" if new_bsr < old_bsr else "declined"

        title = f"BSR Alert: {product.title[:50]}..."
        message = (
            f"The Best Seller Rank of {product.title} has {change_direction} by {abs(bsr_change):.1f}%.\n\n"
            f"Previous rank: #{old_bsr:,}\n"
            f"Current rank: #{new_bsr:,}\n"
            f"Change: {abs(new_bsr - old_bsr):,} positions"
        )

        notification = Notification(
            user_id=user.id,
            notification_type="bsr_change",
            title=title,
            message=message,
            product_id=product.id,
            data={
                "old_bsr": old_bsr,
                "new_bsr": new_bsr,
                "change_percentage": bsr_change,
                "threshold": threshold,
            },
            priority="high" if abs(bsr_change) > threshold * 2 else "normal",
            action_url=f"/products/{product.id}",
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        return notification

    @classmethod
    async def create_stock_change_notification(
        cls,
        db: AsyncSession,
        user: User,
        product: Product,
        old_status: str,
        new_status: str,
    ) -> Notification | None:
        """Create a stock status change notification."""
        stmt = select(UserSettings).where(UserSettings.user_id == user.id)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings:
            settings = UserSettings(user_id=user.id)
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

        if not settings.email_notifications_enabled or not settings.stock_alert_emails:
            return None

        title = f"Stock Alert: {product.title[:50]}..."
        message = (
            f"The stock status of {product.title} has changed.\n\n"
            f"Previous status: {old_status}\n"
            f"Current status: {new_status}"
        )

        # Prioritize "out of stock" alerts
        priority = "urgent" if "out of stock" in new_status.lower() else "normal"

        notification = Notification(
            user_id=user.id,
            notification_type="stock_change",
            title=title,
            message=message,
            product_id=product.id,
            data={
                "old_status": old_status,
                "new_status": new_status,
            },
            priority=priority,
            action_url=f"/products/{product.id}",
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        return notification

    @classmethod
    async def create_system_notification(
        cls,
        db: AsyncSession,
        user: User,
        title: str,
        message: str,
        priority: str = "normal",
        action_url: str | None = None,
    ) -> Notification:
        """Create a system notification."""
        notification = Notification(
            user_id=user.id,
            notification_type="system",
            title=title,
            message=message,
            priority=priority,
            action_url=action_url,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        return notification

    @classmethod
    async def get_unread_count(cls, db: AsyncSession, user: User) -> int:
        """Get count of unread notifications for a user."""
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False))
        )
        result = await db.execute(stmt)
        count = result.scalar_one()
        return count

    @classmethod
    async def mark_all_as_read(cls, db: AsyncSession, user: User) -> int:
        """Mark all notifications as read for a user.

        Returns:
            Number of notifications marked as read
        """
        from datetime import datetime

        from sqlalchemy import update

        stmt = (
            update(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=datetime.utcnow())
        )
        result = await db.execute(stmt)
        await db.commit()
        return int(result.rowcount)  # type: ignore[attr-defined]

    @classmethod
    async def delete_old_notifications(cls, db: AsyncSession, days: int = 30) -> int:
        """Delete notifications older than specified days.

        Args:
            days: Number of days to keep notifications

        Returns:
            Number of notifications deleted
        """
        from datetime import datetime, timedelta

        from sqlalchemy import delete

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = delete(Notification).where(Notification.created_at < cutoff_date)
        result = await db.execute(stmt)
        await db.commit()
        return int(result.rowcount)  # type: ignore[attr-defined]
