"""Pydantic schemas for AI suggestion system."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SuggestionActionOut(BaseModel):
    """Schema for suggestion action output."""

    id: UUID
    action_type: str
    target_field: str
    current_value: str | None
    proposed_value: str
    reasoning: str
    impact_description: str | None
    status: str
    reviewed_at: datetime | None
    applied_at: datetime | None
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)


class SuggestionOut(BaseModel):
    """Schema for suggestion output."""

    id: UUID
    title: str
    description: str
    reasoning: str
    product_id: UUID | None
    priority: str
    category: str
    status: str
    reviewed_at: datetime | None
    ai_model: str
    confidence_score: float | None
    expires_at: datetime | None
    estimated_impact: dict | None
    created_at: datetime
    updated_at: datetime
    # Nested actions
    actions: list[SuggestionActionOut] = []

    model_config = ConfigDict(from_attributes=True)


class SuggestionListOut(BaseModel):
    """Schema for suggestion list item (lighter version)."""

    id: UUID
    title: str
    description: str
    product_id: UUID | None
    priority: str
    category: str
    status: str
    confidence_score: float | None
    created_at: datetime
    action_count: int
    pending_action_count: int

    model_config = ConfigDict(from_attributes=True)


class ActionApprovalRequest(BaseModel):
    """Schema for approving/declining an action."""

    action_ids: list[UUID] = Field(description="List of action IDs to approve/decline")
    decision: str = Field(description="Decision: 'approved' or 'declined'")
    apply_immediately: bool = Field(
        default=False, description="If true, apply approved actions immediately"
    )


class SuggestionApprovalRequest(BaseModel):
    """Schema for approving/declining entire suggestion."""

    suggestion_id: UUID
    decision: str = Field(description="Decision: 'approved', 'declined', or 'partially_approved'")
    approved_action_ids: list[UUID] = Field(
        default=[], description="If partially approving, list of action IDs to approve"
    )
    declined_action_ids: list[UUID] = Field(
        default=[], description="If partially declining, list of action IDs to decline"
    )
    apply_immediately: bool = Field(default=False, description="Apply approved actions immediately")


class ApplyActionRequest(BaseModel):
    """Schema for applying approved actions."""

    action_ids: list[int] = Field(description="List of action IDs to apply")


class SuggestionStats(BaseModel):
    """Schema for suggestion statistics."""

    total_suggestions: int
    pending: int
    approved: int
    rejected: int
    partially_approved: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
