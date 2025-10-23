"""Notification models using SQLAlchemy."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BaseModel

if TYPE_CHECKING:
    from products.models import Product
    from users.models import User


class Notification(BaseModel):
    """User notifications for product alerts and system messages.

    Stores notifications for price changes, BSR changes, stock status updates,
    and other important events that users need to be aware of.
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_product_id", "product_id"),
        Index("idx_notifications_created_at", "created_at"),
        Index("idx_notifications_is_read", "is_read"),
        Index("idx_notifications_type", "notification_type"),
    )

    # User relationship
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="User who receives this notification",
    )

    # Product relationship (optional - some notifications may not be product-specific)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,
        comment="Related product (if applicable)",
    )

    # Notification type
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of notification (e.g., 'price_change', 'system')",
    )

    # Notification content
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="Notification title")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="Notification message")

    # Notification metadata
    data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Additional data (old_price, new_price, etc.)",
    )

    # Priority level
    priority: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False,
        comment="Priority: low, normal, high, urgent",
    )

    # Status tracking
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether notification has been read",
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When notification was marked as read",
    )

    # Email tracking
    email_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Whether email was sent"
    )
    email_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When email was sent"
    )
    email_error: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Error message if email failed"
    )

    # Action link (optional)
    action_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="URL for action button"
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="notifications",
    )
    product: Mapped[Product | None] = relationship(
        "Product",
        back_populates="notifications",
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.notification_type}, title={self.title})>"
