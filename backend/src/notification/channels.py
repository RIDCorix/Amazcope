from .models import Notification


class NotificationChannel:
    async def send_notification(self, notification: Notification) -> None:
        """Send a notification through this channel."""
        pass
