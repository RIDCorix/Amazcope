"""API endpoints for user settings."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, get_current_user
from users.models import User, UserSettings
from users.schemas import UserSettingsOut, UserSettingsUpdate

router = APIRouter()


@router.get("/settings", response_model=UserSettingsOut)
async def get_user_settings(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user's settings.

    Returns:
        User settings object
    """
    # Try to get existing settings
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalar_one_or_none()

    # Create default settings if not exist
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.patch("/settings", response_model=UserSettingsOut)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update current user's settings.

    Args:
        settings_update: Settings fields to update (only provided fields will be updated)
        current_user: Current authenticated user

    Returns:
        Updated settings object
    """
    # Get or create settings
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True)

    if update_data:
        for field, value in update_data.items():
            setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    return settings


@router.post("/settings/reset", response_model=UserSettingsOut)
async def reset_user_settings(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Reset user settings to defaults.

    Deletes current settings and creates new default settings.

    Returns:
        New default settings object
    """
    # Delete existing settings
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    existing_settings = result.scalar_one_or_none()

    if existing_settings:
        await db.delete(existing_settings)
        await db.commit()  # Commit deletion before creating new settings

    # Create new default settings
    settings = UserSettings(user_id=current_user.id)
    db.add(settings)
    await db.commit()
    await db.refresh(settings)

    return settings
