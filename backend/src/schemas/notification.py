"""Pydantic schemas for notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    """Schema for creating a notification."""

    notification_type: str = Field(..., max_length=50, alias="type")
    title: str = Field(..., max_length=255)
    message: str
    product_id: UUID | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$")
    action_url: str | None = Field(None, max_length=500)

    model_config = ConfigDict(populate_by_name=True)


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""

    is_read: bool | None = None
    read_at: datetime | None = None


class NotificationFilter(BaseModel):
    """Schema for filtering notifications."""

    notification_type: str | None = Field(None, alias="type")
    is_read: bool | None = None
    priority: str | None = None
    product_id: UUID | None = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)

    model_config = ConfigDict(populate_by_name=True)


class NotificationOut(BaseModel):
    """Schema for full notification response."""

    id: UUID
    user_id: UUID
    notification_type: str = Field(..., alias="type")
    title: str
    message: str
    product_id: UUID | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    priority: str
    action_url: str | None = None
    is_read: bool = False
    read_at: datetime | None = None
    email_sent: bool = False
    email_sent_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NotificationList(BaseModel):
    """Schema for abbreviated notification list (excludes message and data)."""

    id: UUID
    user_id: UUID
    notification_type: str = Field(..., alias="type")
    title: str
    product_id: UUID | None = None
    priority: str
    action_url: str | None = None
    is_read: bool = False
    read_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
