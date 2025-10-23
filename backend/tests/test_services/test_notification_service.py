"""Tests for NotificationService."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from notification.models import Notification
from products.models import Product
from services.notification_service import NotificationService
from users.models import User, UserSettings


class TestNotificationTypes:
    """Test notification type constants."""

    def test_notification_types_defined(self):
        """Test that notification types are properly defined."""
        types = NotificationService.NOTIFICATION_TYPES

        assert "price_change" in types
        assert "bsr_change" in types
        assert "stock_change" in types
        assert "system" in types
        assert "daily_summary" in types
        assert "weekly_report" in types

    def test_notification_type_labels(self):
        """Test notification type labels are user-friendly."""
        types = NotificationService.NOTIFICATION_TYPES

        assert types["price_change"] == "Price Change Alert"
        assert types["bsr_change"] == "BSR Change Alert"
        assert types["stock_change"] == "Stock Status Alert"


class TestPriceChangeNotifications:
    """Test price change notification creation."""

    @pytest.mark.asyncio
    async def test_create_price_increase_notification(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_product: Product,
    ):
        """Test creating notification for price increase."""
        # Enable notifications
        settings = UserSettings(
            user_id=test_user.id,
            email_notifications_enabled=True,
            price_alert_emails=True,
        )
        db_session.add(settings)
        await db_session.commit()

        old_price = 29.99
        new_price = 34.99
        threshold = 10.0

        notification = await NotificationService.create_price_change_notification(
            db=db_session,
            user=test_user,
            product=test_product,
            old_price=old_price,
            new_price=new_price,
            threshold=threshold,
        )

        assert notification is not None
        assert notification.user_id == test_user.id
        assert notification.product_id == test_product.id
        assert notification.notification_type == "price_change"
        assert "increased" in notification.message
        assert "$29.99" in notification.message
        assert "$34.99" in notification.message
        assert notification.priority in ["normal", "high"]

    @pytest.mark.asyncio
    async def test_create_price_decrease_notification(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_product: Product,
    ):
        """Test creating notification for price decrease."""
        settings = UserSettings(
            user_id=test_user.id,
            email_notifications_enabled=True,
            price_alert_emails=True,
        )
        db_session.add(settings)
        await db_session.commit()

        old_price = 29.99
        new_price = 24.99
        threshold = 10.0

        notification = await NotificationService.create_price_change_notification(
            db=db_session,
            user=test_user,
            product=test_product,
            old_price=old_price,
            new_price=new_price,
            threshold=threshold,
        )

        assert notification is not None
        assert "decreased" in notification.message
        assert notification.data["change_percentage"] < 0

    @pytest.mark.asyncio
    async def test_price_notification_disabled(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_product: Product,
    ):
        """Test no notification when price alerts disabled."""
        settings = UserSettings(
            user_id=test_user.id,
            email_notifications_enabled=False,  # Disabled
            price_alert_emails=False,
        )
        db_session.add(settings)
        await db_session.commit()

        notification = await NotificationService.create_price_change_notification(
            db=db_session,
            user=test_user,
            product=test_product,
            old_price=29.99,
            new_price=34.99,
            threshold=10.0,
        )

        assert notification is None

    @pytest.mark.asyncio
    async def test_price_notification_high_priority(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_product: Product,
    ):
        """Test high priority for large price changes."""
        settings = UserSettings(
            user_id=test_user.id,
            email_notifications_enabled=True,
            price_alert_emails=True,
        )
        db_session.add(settings)
        await db_session.commit()

        # 50% price increase (>2x threshold of 10%)
        old_price = 20.00
        new_price = 30.00
        threshold = 10.0

        notification = await NotificationService.create_price_change_notification(
            db=db_session,
            user=test_user,
            product=test_product,
            old_price=old_price,
            new_price=new_price,
            threshold=threshold,
        )

        assert notification is not None
        assert notification.priority == "high"


class TestBSRChangeNotifications:
    """Test BSR change notification creation."""

    @pytest.mark.asyncio
    async def test_create_bsr_improvement_notification(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_product: Product,
    ):
        """Test notification for BSR improvement (lower rank)."""
        settings = UserSettings(
            user_id=test_user.id,
            email_notifications_enabled=True,
            bsr_alert_emails=True,
        )
        db_session.add(settings)
        await db_session.commit()

        old_bsr = 1000
        new_bsr = 600  # Improved
        threshold = 30.0

        notification = await NotificationService.create_bsr_change_notification(
            db=db_session,
            user=test_user,
            product=test_product,
            old_bsr=old_bsr,
            new_bsr=new_bsr,
            threshold=threshold,
        )

        assert notification is not None
        assert notification.notification_type == "bsr_change"
        assert "improved" in notification.message
        assert "#1,000" in notification.message or "1,000" in notification.message
        assert "#600" in notification.message or "600" in notification.message

    @pytest.mark.asyncio
    async def test_create_bsr_decline_notification(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_product: Product,
    ):
        """Test notification for BSR decline (higher rank)."""
        settings = UserSettings(
            user_id=test_user.id,
            email_notifications_enabled=True,
            bsr_alert_emails=True,
        )
        db_session.add(settings)
        await db_session.commit()

        old_bsr = 1000
        new_bsr = 1500  # Declined
        threshold = 30.0

        notification = await NotificationService.create_bsr_change_notification(
            db=db_session,
            user=test_user,
            product=test_product,
            old_bsr=old_bsr,
            new_bsr=new_bsr,
            threshold=threshold,
        )

        assert notification is not None
        assert "declined" in notification.message

    @pytest.mark.asyncio
    async def test_bsr_notification_disabled(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_product: Product,
    ):
        """Test no notification when BSR alerts disabled."""
        settings = UserSettings(
            user_id=test_user.id,
            email_notifications_enabled=True,
            bsr_alert_emails=False,  # Disabled
        )
        db_session.add(settings)
        await db_session.commit()

        notification = await NotificationService.create_bsr_change_notification(
            db=db_session,
            user=test_user,
            product=test_product,
            old_bsr=1000,
            new_bsr=600,
            threshold=30.0,
        )

        assert notification is None


class TestStockChangeNotifications:
    """Test stock change notification creation."""

    @pytest.mark.asyncio
    async def test_create_out_of_stock_notification(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_product: Product,
    ):
        """Test urgent notification when product goes out of stock."""
        settings = UserSettings(
            user_id=test_user.id,
            email_notifications_enabled=True,
            stock_alert_emails=True,
        )
        db_session.add(settings)
        await db_session.commit()

        notification = await NotificationService.create_stock_change_notification(
            db=db_session,
            user=test_user,
            product=test_product,
            old_status="In Stock",
            new_status="Out of Stock",
        )

        assert notification is not None
        assert notification.notification_type == "stock_change"
        assert notification.priority == "urgent"
        assert "Out of Stock" in notification.message

    @pytest.mark.asyncio
    async def test_create_back_in_stock_notification(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_product: Product,
    ):
        """Test notification when product comes back in stock."""
        settings = UserSettings(
            user_id=test_user.id,
            email_notifications_enabled=True,
            stock_alert_emails=True,
        )
        db_session.add(settings)
        await db_session.commit()

        notification = await NotificationService.create_stock_change_notification(
            db=db_session,
            user=test_user,
            product=test_product,
            old_status="Out of Stock",
            new_status="In Stock",
        )

        assert notification is not None
        assert notification.priority == "normal"


class TestSystemNotifications:
    """Test system notification creation."""

    @pytest.mark.asyncio
    async def test_create_system_notification(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test creating a system notification."""
        title = "Welcome to Amazcope!"
        message = "Your account has been successfully created."

        notification = await NotificationService.create_system_notification(
            db=db_session,
            user=test_user,
            title=title,
            message=message,
            priority="normal",
        )

        assert notification is not None
        assert notification.user_id == test_user.id
        assert notification.notification_type == "system"
        assert notification.title == title
        assert notification.message == message
        assert notification.priority == "normal"

    @pytest.mark.asyncio
    async def test_create_system_notification_with_action(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test system notification with action URL."""
        notification = await NotificationService.create_system_notification(
            db=db_session,
            user=test_user,
            title="Update Available",
            message="A new feature is available!",
            priority="high",
            action_url="/settings/features",
        )

        assert notification.action_url == "/settings/features"
        assert notification.priority == "high"


class TestUnreadCount:
    """Test unread notification count."""

    @pytest.mark.asyncio
    async def test_get_unread_count_zero(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test unread count when no notifications exist."""
        count = await NotificationService.get_unread_count(db_session, test_user)
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_unread_count_with_notifications(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test unread count with multiple unread notifications."""
        # Create 3 unread notifications
        for i in range(3):
            notif = Notification(
                user_id=test_user.id,
                notification_type="system",
                title=f"Test {i}",
                message="Test message",
                is_read=False,
            )
            db_session.add(notif)

        await db_session.commit()

        count = await NotificationService.get_unread_count(db_session, test_user)
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_unread_count_excludes_read(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test unread count excludes already read notifications."""
        # Create 2 unread and 2 read notifications
        for i in range(4):
            notif = Notification(
                user_id=test_user.id,
                notification_type="system",
                title=f"Test {i}",
                message="Test message",
                is_read=(i < 2),  # First 2 are read
            )
            db_session.add(notif)

        await db_session.commit()

        count = await NotificationService.get_unread_count(db_session, test_user)
        assert count == 2


class TestMarkAllAsRead:
    """Test marking all notifications as read."""

    @pytest.mark.asyncio
    async def test_mark_all_as_read_success(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test marking multiple unread notifications as read."""
        # Create 5 unread notifications
        for i in range(5):
            notif = Notification(
                user_id=test_user.id,
                notification_type="system",
                title=f"Test {i}",
                message="Test message",
                is_read=False,
            )
            db_session.add(notif)

        await db_session.commit()

        # Mark all as read
        count = await NotificationService.mark_all_as_read(db_session, test_user)
        assert count == 5

        # Verify unread count is now 0
        unread = await NotificationService.get_unread_count(db_session, test_user)
        assert unread == 0

    @pytest.mark.asyncio
    async def test_mark_all_as_read_empty(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test marking as read when no unread notifications exist."""
        count = await NotificationService.mark_all_as_read(db_session, test_user)
        assert count == 0


class TestDeleteOldNotifications:
    """Test deleting old notifications."""

    @pytest.mark.asyncio
    async def test_delete_old_notifications(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test deleting notifications older than cutoff date."""
        # Create old notification (40 days ago)
        old_notif = Notification(
            user_id=test_user.id,
            notification_type="system",
            title="Old notification",
            message="This is old",
            created_at=datetime.utcnow() - timedelta(days=40),
        )
        db_session.add(old_notif)

        # Create recent notification (10 days ago)
        recent_notif = Notification(
            user_id=test_user.id,
            notification_type="system",
            title="Recent notification",
            message="This is recent",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        db_session.add(recent_notif)

        await db_session.commit()

        # Delete notifications older than 30 days
        deleted_count = await NotificationService.delete_old_notifications(db_session, days=30)

        assert deleted_count == 1

    @pytest.mark.asyncio
    async def test_delete_old_notifications_custom_days(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test deleting notifications with custom retention period."""
        # Create notifications at different ages
        for days_ago in [5, 10, 15, 20]:
            notif = Notification(
                user_id=test_user.id,
                notification_type="system",
                title=f"Notification {days_ago}",
                message="Test",
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db_session.add(notif)

        await db_session.commit()

        # Delete notifications older than 12 days
        deleted_count = await NotificationService.delete_old_notifications(db_session, days=12)

        # Should delete the 15-day and 20-day old notifications
        assert deleted_count == 2
