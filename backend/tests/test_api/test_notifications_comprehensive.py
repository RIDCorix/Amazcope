"""Comprehensive tests for notification API endpoints.

Tests notification operations including:
- Listing notifications with filters
- Getting unread count
- Marking notifications as read
- Deleting notifications
- Bulk operations
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from notification.models import Notification
from users.models import User


class TestListNotifications:
    """Tests for listing notifications."""

    @pytest.mark.asyncio
    async def test_list_notifications_success(
        self,
        client: AsyncClient,
        test_notification: Notification,
        auth_headers: dict[str, str],
    ):
        """Test successful notification listing."""
        response = await client.get(
            "/api/v1/notifications/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert any(n["id"] == str(test_notification.id) for n in data)

    @pytest.mark.asyncio
    async def test_list_notifications_filter_unread(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test filtering notifications by read status."""
        # Create read and unread notifications
        unread_notif = Notification(
            user_id=test_user.id,
            title="Unread Notification",
            message="This is unread",
            notification_type="info",
            is_read=False,
        )
        read_notif = Notification(
            user_id=test_user.id,
            title="Read Notification",
            message="This is read",
            notification_type="info",
            is_read=True,
        )
        db_session.add_all([unread_notif, read_notif])
        await db_session.commit()

        response = await client.get(
            "/api/v1/notifications/?is_read=false",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned notifications should be unread
        assert all(not n.get("is_read", True) for n in data)

    @pytest.mark.asyncio
    async def test_list_notifications_pagination(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test notification pagination."""
        response = await client.get(
            "/api/v1/notifications/?skip=0&limit=5",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_list_notifications_unauthorized(self, client: AsyncClient):
        """Test listing notifications requires authentication."""
        response = await client.get("/api/v1/notifications/")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_notifications_user_isolation(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test users can only see their own notifications."""
        # Create another user with notifications
        other_user = User(
            email="other2@example.com",
            username="otheruser2",
            hashed_password="hashedpassword",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_notif = Notification(
            user_id=other_user.id,
            title="Other User Notification",
            message="Should not be visible",
            notification_type="info",
            is_read=False,
        )
        db_session.add(other_notif)
        await db_session.commit()

        # Get test_user's notifications
        response = await client.get(
            "/api/v1/notifications/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should not contain other user's notification
        assert not any(n["id"] == other_notif.id for n in data)


class TestGetUnreadCount:
    """Tests for getting unread notification count."""

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test getting unread notification count."""
        # Create multiple unread notifications
        for i in range(3):
            notif = Notification(
                user_id=test_user.id,
                title=f"Unread {i}",
                message=f"Message {i}",
                notification_type="info",
                is_read=False,
            )
            db_session.add(notif)
        await db_session.commit()

        response = await client.get(
            "/api/v1/notifications/unread-count",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data or "unread_count" in data
        count = data.get("count") or data.get("unread_count")
        assert count >= 3

    @pytest.mark.asyncio
    async def test_get_unread_count_unauthorized(self, client: AsyncClient):
        """Test getting unread count requires authentication."""
        response = await client.get("/api/v1/notifications/unread-count")

        assert response.status_code == 403


class TestGetNotificationDetails:
    """Tests for getting single notification details."""

    @pytest.mark.asyncio
    async def test_get_notification_success(
        self,
        client: AsyncClient,
        test_notification: Notification,
        auth_headers: dict[str, str],
    ):
        """Test getting notification details."""
        response = await client.get(
            f"/api/v1/notifications/{test_notification.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_notification.id)
        assert data["title"] == test_notification.title

    @pytest.mark.asyncio
    async def test_get_notification_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test getting non-existent notification returns 404."""
        from uuid import uuid4

        fake_uuid = uuid4()
        response = await client.get(
            f"/api/v1/notifications/{fake_uuid}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_notification_not_owned(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test cannot get notification owned by another user."""
        # Create another user with notification
        other_user = User(
            email="other3@example.com",
            username="otheruser3",
            hashed_password="hashedpassword",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_notif = Notification(
            user_id=other_user.id,
            title="Other Notification",
            message="Not accessible",
            notification_type="info",
            is_read=False,
        )
        db_session.add(other_notif)
        await db_session.commit()
        await db_session.refresh(other_notif)

        response = await client.get(
            f"/api/v1/notifications/{other_notif.id}",
            headers=auth_headers,
        )

        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_get_notification_unauthorized(
        self, client: AsyncClient, test_notification: Notification
    ):
        """Test getting notification requires authentication."""
        response = await client.get(f"/api/v1/notifications/{test_notification.id}")

        assert response.status_code in [401, 403]


class TestUpdateNotification:
    """Tests for updating/marking notifications as read."""

    @pytest.mark.asyncio
    async def test_mark_notification_as_read(
        self,
        client: AsyncClient,
        test_notification: Notification,
        auth_headers: dict[str, str],
    ):
        """Test marking notification as read."""
        response = await client.patch(
            f"/api/v1/notifications/{test_notification.id}",
            headers=auth_headers,
            json={"is_read": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True

    @pytest.mark.asyncio
    async def test_mark_notification_as_unread(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test marking notification as unread."""
        # Create a read notification
        read_notif = Notification(
            user_id=test_user.id,
            title="Read Notification",
            message="Already read",
            notification_type="info",
            is_read=True,
        )
        db_session.add(read_notif)
        await db_session.commit()
        await db_session.refresh(read_notif)

        response = await client.patch(
            f"/api/v1/notifications/{read_notif.id}",
            headers=auth_headers,
            json={"is_read": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is False

    @pytest.mark.asyncio
    async def test_update_notification_not_owned(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test cannot update notification owned by another user."""
        # Create another user with notification
        other_user = User(
            email="other4@example.com",
            username="otheruser4",
            hashed_password="hashedpassword",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_notif = Notification(
            user_id=other_user.id,
            title="Other Notification",
            message="Not accessible",
            notification_type="info",
            is_read=False,
        )
        db_session.add(other_notif)
        await db_session.commit()
        await db_session.refresh(other_notif)

        response = await client.patch(
            f"/api/v1/notifications/{other_notif.id}",
            headers=auth_headers,
            json={"is_read": True},
        )

        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_update_notification_unauthorized(
        self, client: AsyncClient, test_notification: Notification
    ):
        """Test updating notification requires authentication."""
        response = await client.patch(
            f"/api/v1/notifications/{test_notification.id}",
            json={"is_read": True},
        )

        assert response.status_code in [401, 403]


class TestMarkAllRead:
    """Tests for marking all notifications as read."""

    @pytest.mark.asyncio
    async def test_mark_all_read_success(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test marking all notifications as read."""
        # Create multiple unread notifications
        for i in range(5):
            notif = Notification(
                user_id=test_user.id,
                title=f"Unread {i}",
                message=f"Message {i}",
                notification_type="info",
                is_read=False,
            )
            db_session.add(notif)
        await db_session.commit()

        response = await client.post(
            "/api/v1/notifications/mark-all-read",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data or "updated" in data or "message" in data

        # Verify all are marked as read
        unread_response = await client.get(
            "/api/v1/notifications/?is_read=false",
            headers=auth_headers,
        )
        assert unread_response.status_code == 200
        unread_data = unread_response.json()
        assert len(unread_data) == 0

    @pytest.mark.asyncio
    async def test_mark_all_read_unauthorized(self, client: AsyncClient):
        """Test marking all as read requires authentication."""
        response = await client.post("/api/v1/notifications/mark-all-read")

        assert response.status_code == 403


class TestDeleteNotification:
    """Tests for deleting single notification."""

    @pytest.mark.asyncio
    async def test_delete_notification_success(
        self,
        client: AsyncClient,
        test_notification: Notification,
        auth_headers: dict[str, str],
    ):
        """Test deleting a notification."""
        response = await client.delete(
            f"/api/v1/notifications/{test_notification.id}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 204]

        # Verify deleted
        verify_response = await client.get(
            f"/api/v1/notifications/{test_notification.id}",
            headers=auth_headers,
        )
        assert verify_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_notification_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test deleting non-existent notification returns 404."""
        from uuid import uuid4

        fake_uuid = uuid4()
        response = await client.delete(
            f"/api/v1/notifications/{fake_uuid}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_notification_not_owned(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test cannot delete notification owned by another user."""
        # Create another user with notification
        other_user = User(
            email="other5@example.com",
            username="otheruser5",
            hashed_password="hashedpassword",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_notif = Notification(
            user_id=other_user.id,
            title="Other Notification",
            message="Not accessible",
            notification_type="info",
            is_read=False,
        )
        db_session.add(other_notif)
        await db_session.commit()
        await db_session.refresh(other_notif)

        response = await client.delete(
            f"/api/v1/notifications/{other_notif.id}",
            headers=auth_headers,
        )

        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_delete_notification_unauthorized(
        self, client: AsyncClient, test_notification: Notification
    ):
        """Test deleting notification requires authentication."""
        response = await client.delete(f"/api/v1/notifications/{test_notification.id}")

        assert response.status_code in [401, 403]


class TestDeleteAllNotifications:
    """Tests for deleting all notifications."""

    @pytest.mark.asyncio
    async def test_delete_all_notifications_success(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test deleting all user's notifications."""
        # Create multiple notifications
        for i in range(5):
            notif = Notification(
                user_id=test_user.id,
                title=f"Notification {i}",
                message=f"Message {i}",
                notification_type="info",
                is_read=False,
            )
            db_session.add(notif)
        await db_session.commit()

        response = await client.delete(
            "/api/v1/notifications/",
            headers=auth_headers,
        )

        assert response.status_code in [200, 204]

        # Verify all deleted
        list_response = await client.get(
            "/api/v1/notifications/",
            headers=auth_headers,
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_delete_all_notifications_unauthorized(self, client: AsyncClient):
        """Test deleting all notifications requires authentication."""
        response = await client.delete("/api/v1/notifications/")

        assert response.status_code == 403


class TestSendTestNotification:
    """Tests for sending test notification."""

    @pytest.mark.asyncio
    async def test_send_test_notification(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test sending a test notification."""
        response = await client.post(
            "/api/v1/notifications/test",
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert "title" in data or "message" in data

    @pytest.mark.asyncio
    async def test_send_test_notification_unauthorized(self, client: AsyncClient):
        """Test sending test notification requires authentication."""
        response = await client.post("/api/v1/notifications/test")

        assert response.status_code == 403


class TestNotificationFlow:
    """Integration tests for complete notification workflows."""

    @pytest.mark.asyncio
    async def test_complete_notification_flow(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test complete notification flow: create → list → read → mark read → delete."""
        # 1. Create notification
        notif = Notification(
            user_id=test_user.id,
            title="Flow Test Notification",
            message="This is a test notification",
            notification_type="info",
            is_read=False,
        )
        db_session.add(notif)
        await db_session.commit()
        await db_session.refresh(notif)

        # 2. List notifications (should include new one)
        list_response = await client.get(
            "/api/v1/notifications/",
            headers=auth_headers,
        )
        assert list_response.status_code == 200
        notifications = list_response.json()
        assert any(n["id"] == str(notif.id) for n in notifications)

        # 3. Get unread count
        count_response = await client.get(
            "/api/v1/notifications/unread-count",
            headers=auth_headers,
        )
        assert count_response.status_code == 200
        count_data = count_response.json()
        assert (count_data.get("count") or count_data.get("unread_count")) > 0

        # 4. Read notification details
        detail_response = await client.get(
            f"/api/v1/notifications/{notif.id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200

        # 5. Mark as read
        mark_read_response = await client.patch(
            f"/api/v1/notifications/{notif.id}",
            headers=auth_headers,
            json={"is_read": True},
        )
        assert mark_read_response.status_code == 200

        # 6. Delete notification
        delete_response = await client.delete(
            f"/api/v1/notifications/{notif.id}",
            headers=auth_headers,
        )
        assert delete_response.status_code in [200, 204]

        # 7. Verify deleted
        verify_response = await client.get(
            f"/api/v1/notifications/{notif.id}",
            headers=auth_headers,
        )
        assert verify_response.status_code == 404
