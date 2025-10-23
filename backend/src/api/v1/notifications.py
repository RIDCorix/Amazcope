from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, get_current_user
from notification.models import Notification
from schemas.notification import (
    NotificationOut,
    NotificationUpdate,
)
from services.notification_service import NotificationService
from users.models import User

router = APIRouter()


@router.get("/", response_model=list[NotificationOut])  # type: ignore[valid-type]
async def get_notifications(
    is_read: bool | None = Query(None, description="Filter by read status"),
    notification_type: str | None = Query(None, description="Filter by type"),
    priority: str | None = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get user's notifications with optional filters.

    Returns paginated list of notifications ordered by creation date (newest first).
    """
    query = select(Notification).where(Notification.user_id == current_user.id)

    # Apply filters
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)

    if notification_type:
        query = query.where(Notification.notification_type == notification_type)

    if priority:
        query = query.where(Notification.priority == priority)

    # Fetch with pagination
    result = await db.execute(query.offset(offset).limit(limit))
    notifications = result.scalars().all()

    return [NotificationOut.model_validate(n) for n in notifications]


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, int]:
    """Get count of unread notifications for current user."""
    count = await NotificationService.get_unread_count(db, current_user)
    return {"count": count}


@router.get("/{notification_id}", response_model=NotificationOut)
async def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get a specific notification by ID."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationOut.model_validate(notification)


@router.patch("/{notification_id}", response_model=NotificationOut)
async def update_notification(
    notification_id: UUID,
    update_data: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Update a notification (mark as read/unread)."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Update fields
    if update_data.is_read is not None:
        if update_data.is_read:
            notification.is_read = True
            from datetime import UTC, datetime

            notification.read_at = datetime.now(UTC)
        else:
            notification.is_read = False
            notification.read_at = None  # type: ignore[assignment]
            await db.commit()
            await db.refresh(notification)

    return NotificationOut.model_validate(notification)


@router.post("/mark-all-read", response_model=dict)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Mark all notifications as read for current user."""
    updated_count = await NotificationService.mark_all_as_read(db, current_user)
    return {
        "message": f"Marked {updated_count} notifications as read",
        "count": updated_count,
    }


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, str]:
    """Delete a specific notification."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.delete(notification)
    await db.commit()

    return {"message": "Notification deleted successfully"}


@router.delete("/", response_model=dict)
async def delete_all_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Delete all notifications for current user."""
    result = await db.execute(select(Notification).where(Notification.user_id == current_user.id))
    notifications_to_delete = result.scalars().all()
    for notification in notifications_to_delete:
        await db.delete(notification)
    await db.commit()
    deleted_count = len(notifications_to_delete)

    return {
        "message": f"Deleted {deleted_count} notifications",
        "count": deleted_count,
    }


@router.post("/test", response_model=NotificationOut)
async def create_test_notification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Create a test notification (for development/testing)."""
    notification = await NotificationService.create_system_notification(
        db=db,
        user=current_user,
        title="Test Notification",
        message="This is a test notification to verify the system is working correctly.",
        priority="normal",
        action_url="/settings",
    )

    return NotificationOut.model_validate(notification)
