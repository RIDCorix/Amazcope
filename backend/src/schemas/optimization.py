"""Pydantic schemas for optimization suggestions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OptimizationSuggestionOut(BaseModel):
    """Schema for full optimization suggestion response."""

    id: UUID
    product_id: UUID
    user_id: UUID
    suggestion_type: str
    priority: str
    title: str
    description: str
    reasoning: str
    current_value: str | None = None
    suggested_value: str | None = None
    expected_impact: str | None = None
    impact_score: float
    effort_score: float
    confidence_score: float
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime | None = None
    implemented_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ABTestOut(BaseModel):
    """Schema for A/B test response."""

    id: UUID
    product_id: UUID
    user_id: UUID
    suggestion_id: UUID | None = None
    name: str
    description: str | None = None
    test_type: str
    status: str
    control_variant: dict[str, Any]
    test_variant: dict[str, Any]
    baseline_metrics: dict[str, Any] = Field(default_factory=dict)
    control_metrics: dict[str, Any] = Field(default_factory=dict)
    test_metrics: dict[str, Any] = Field(default_factory=dict)
    sample_size: int = 0
    started_at: datetime
    ended_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SuggestionCreate(BaseModel):
    """Request to generate optimization suggestions for a product."""

    product_id: UUID
    include_competitors: bool = True  # Include competitor analysis
    suggestion_types: list[str] | None = Field(
        None,
        description="Specific types to generate (title, pricing, description, images, keywords)",
    )


class SuggestionResponse(BaseModel):
    """Individual optimization suggestion."""

    suggestion_type: str
    priority: str
    title: str
    description: str
    reasoning: str
    current_value: str | None = None
    suggested_value: str | None = None
    expected_impact: str | None = None
    impact_score: float
    effort_score: float
    confidence_score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizationReport(BaseModel):
    """Complete optimization report for a product."""

    product_id: UUID
    product_title: str
    generated_at: datetime
    suggestions: list[SuggestionResponse]
    overall_score: float = Field(..., description="Overall listing quality score (0-100)")
    top_priority: str = Field(..., description="Most impactful improvement area")
    cache_hit: bool = Field(False, description="Whether results were cached")


class SuggestionUpdate(BaseModel):
    """Update suggestion status or implementation."""

    status: str | None = Field(None, pattern="^(pending|accepted|rejected|implemented)$")
    implemented_at: datetime | None = None


class ABTestCreate(BaseModel):
    """Create a new A/B test."""

    product_id: UUID
    suggestion_id: UUID | None = None  # Optional: link to a suggestion
    name: str
    description: str | None = None
    test_type: str
    control_variant: dict[str, Any]
    test_variant: dict[str, Any]
    baseline_metrics: dict[str, Any] = Field(default_factory=dict)


class ABTestUpdate(BaseModel):
    """Update A/B test metrics and results."""

    control_metrics: dict[str, Any] | None = None
    test_metrics: dict[str, Any] | None = None
    sample_size: int | None = None
    status: str | None = Field(None, pattern="^(active|completed|cancelled)$")


class ABTestResult(BaseModel):
    """A/B test analysis results."""

    test_id: UUID
    test_name: str
    status: str
    sample_size: int
    control_metrics: dict[str, Any]
    test_metrics: dict[str, Any]
    winner: str | None  # control, test, inconclusive
    confidence_level: float | None
    p_value: float | None
    improvement_percentage: float | None
    recommendation: str  # What action to take based on results
