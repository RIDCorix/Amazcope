"""Alert models using SQLAlchemy."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BaseModel
from core.utils import now

if TYPE_CHECKING:
    from products.models import Product, ProductSnapshot
    from users.models import User


class AlertType:
    """Alert type constants."""

    PRICE_INCREASE = "price_increase"
    PRICE_DECREASE = "price_decrease"
    BSR_IMPROVED = "bsr_improved"  # Rank went down (better)
    BSR_DROPPED = "bsr_dropped"  # Rank went up (worse)
    OUT_OF_STOCK = "out_of_stock"
    BACK_IN_STOCK = "back_in_stock"
    RATING_CHANGED = "rating_changed"
    REVIEW_SPIKE = "review_spike"  # Significant increase in reviews


class AlertSeverity:
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(BaseModel):
    """Alert model for significant product changes.

    Alerts are generated when:
    - Price changes > threshold (default 10%)
    - BSR changes > threshold (default 30%)
    - Stock status changes
    - Significant rating/review changes
    """

    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alerts_user_read", "user_id", "is_read"),
        Index("idx_alerts_product_created", "product_id", "created_at"),
        Index("idx_alerts_severity_read", "severity", "is_read"),
    )

    # Alert metadata
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="Type of alert")
    severity: Mapped[str] = mapped_column(
        String(20), default=AlertSeverity.INFO, nullable=False, comment="Alert severity"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="Alert title")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="Detailed alert message")

    # Change details
    old_value: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Previous value"
    )
    new_value: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="New value")
    change_percentage: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Percentage change if applicable"
    )

    # Alert status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user has read this alert",
    )
    is_dismissed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user dismissed this alert",
    )
    notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=now,
        nullable=True,
        comment="When notification was sent",
    )

    # Relationships
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="Associated product",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Alert recipient",
    )
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        comment="Snapshot that triggered this alert",
    )

    # Relationships
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="alerts",
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="alerts",
    )
    snapshot: Mapped[ProductSnapshot | None] = relationship(
        "ProductSnapshot",
        foreign_keys=[snapshot_id],
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type={self.alert_type}, title={self.title})>"
