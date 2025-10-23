"""Pydantic schemas for UserProduct (product ownership) operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserProductCreate(BaseModel):
    """Schema for claiming a product."""

    product_id: UUID = Field(..., description="Product ID to claim")
    is_primary: bool = Field(default=True, description="Whether this is the user's primary product")
    price_change_threshold: float | None = Field(
        None, description="Custom price change alert threshold (percentage)"
    )
    bsr_change_threshold: float | None = Field(
        None, description="Custom BSR change alert threshold (percentage)"
    )
    notes: str | None = Field(None, description="User's notes about this product")
    tags: list[str] | None = Field(None, description="Custom tags for organization")


class UserProductUpdate(BaseModel):
    """Schema for updating owned product settings."""

    is_primary: bool | None = Field(None, description="Update primary status")
    price_change_threshold: float | None = Field(None, description="Update price threshold")
    bsr_change_threshold: float | None = Field(None, description="Update BSR threshold")
    notes: str | None = Field(None, description="Update notes")
    tags: list[str] | None = Field(None, description="Update tags")


class UserProductOut(BaseModel):
    """Schema for UserProduct response."""

    id: UUID
    user_id: UUID
    product_id: UUID
    claimed_at: datetime
    is_primary: bool
    price_change_threshold: float | None = None
    bsr_change_threshold: float | None = None
    notes: str | None = None
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductWithOwnershipOut(BaseModel):
    """Schema for Product with ownership information."""

    # Product details
    id: UUID
    asin: str
    title: str
    brand: str | None = None
    category: str | None = None
    url: str
    image_url: str | None = None
    is_competitor: bool
    is_active: bool

    # Ownership info
    is_owned: bool = Field(..., description="Whether the current user owns/claimed this product")
    ownership: UserProductOut | None = Field(
        None, description="Ownership details if user owns this product"
    )

    # Latest snapshot data (if available)
    latest_price: float | None = None
    latest_bsr: int | None = None
    latest_rating: float | None = None

    model_config = ConfigDict(from_attributes=True)


class CompetitorProductList(BaseModel):
    """Schema for listing competitor products in a category."""

    total: int
    owned_count: int = Field(..., description="Number of products owned by user")
    competitor_count: int = Field(..., description="Number of competitor products")
    products: list[ProductWithOwnershipOut]


class ClaimProductResponse(BaseModel):
    """Response after claiming a product."""

    success: bool
    message: str
    user_product: UserProductOut
    product_id: UUID
    asin: str
