"""Pydantic schemas for product tracking API."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProductCreate(BaseModel):
    """Schema for creating a new product to track by ASIN."""

    asin: str = Field(..., min_length=10, max_length=10, description="Amazon ASIN")
    price_change_threshold: float = Field(
        10.0, ge=0, le=100, description="Price change threshold %"
    )
    bsr_change_threshold: float = Field(30.0, ge=0, le=100, description="BSR change threshold %")
    category_url: str | None = Field(
        None, description="Amazon category URL for tracking bestsellers"
    )
    manual_category: str | None = Field(
        None, max_length=200, description="Manually specified category name"
    )
    manual_small_category: str | None = Field(
        None, max_length=200, description="Manually specified subcategory name"
    )


class ProductFromUrlCreate(BaseModel):
    """Schema for creating a new product to track from Amazon URL."""

    url: str = Field(..., description="Amazon product URL")
    price_change_threshold: float = Field(
        10.0, ge=0, le=100, description="Price change threshold %"
    )
    bsr_change_threshold: float = Field(30.0, ge=0, le=100, description="BSR change threshold %")
    scrape_reviews: bool = Field(True, description="Whether to scrape product reviews")
    scrape_bestsellers: bool = Field(True, description="Whether to scrape category bestsellers")
    category_url: str | None = Field(
        None, description="Custom category URL (overrides auto-detected)"
    )
    manual_category: str | None = Field(
        None, max_length=200, description="Manually specified category name"
    )
    manual_small_category: str | None = Field(
        None, max_length=200, description="Manually specified subcategory name"
    )

    @field_validator("url", "category_url")
    @classmethod
    def validate_amazon_url(cls, v: str | None) -> str | None:
        """Validate URL is from Amazon."""
        if v and "amazon." not in v.lower():
            raise ValueError("URL must be from Amazon")
        return v


class ProductUpdateCategory(BaseModel):
    """Schema for updating product category."""

    category_url: str | None = Field(None, description="Amazon category URL")
    manual_category: str | None = Field(None, max_length=200, description="Manual category name")
    manual_small_category: str | None = Field(
        None, max_length=200, description="Manual subcategory name"
    )
    trigger_bestsellers_scrape: bool = Field(
        True, description="Whether to trigger bestsellers scraping"
    )

    @field_validator("category_url")
    @classmethod
    def validate_category_url(cls, v: str | None) -> str | None:
        """Validate category URL is from Amazon."""
        if v and "amazon." not in v.lower():
            raise ValueError("Category URL must be from Amazon")
        return v


class ProductUpdate(BaseModel):
    """Schema for updating product details."""

    title: str | None = Field(None, max_length=500, description="Product title")
    brand: str | None = Field(None, max_length=200, description="Brand name")
    category: str | None = Field(None, max_length=200, description="Main category")
    small_category: str | None = Field(None, max_length=200, description="Subcategory")

    # Tracking settings
    is_active: bool | None = Field(None, description="Whether to actively track this product")
    track_frequency: str | None = Field(None, description="Tracking frequency: daily, hourly")

    # Alert thresholds
    price_change_threshold: float | None = Field(
        None, ge=0, le=100, description="Price change threshold %"
    )
    bsr_change_threshold: float | None = Field(
        None, ge=0, le=100, description="BSR change threshold %"
    )

    # Product URLs and metadata
    url: str | None = Field(None, max_length=1000, description="Amazon product URL")
    image_url: str | None = Field(None, max_length=1000, description="Product image URL")

    # Product content (for manual editing)
    product_description: str | None = Field(None, description="Product description")
    features: dict[str, Any] | None = Field(None, description="Product features list")

    @field_validator("url")
    @classmethod
    def validate_amazon_url(cls, v: str | None) -> str | None:
        """Validate URL is from Amazon."""
        if v and "amazon." not in v.lower():
            raise ValueError("URL must be from Amazon")
        return v

    @field_validator("track_frequency")
    @classmethod
    def validate_track_frequency(cls, v: str | None) -> str | None:
        """Validate tracking frequency."""
        if v and v not in ["daily", "hourly"]:
            raise ValueError("Track frequency must be 'daily' or 'hourly'")
        return v


class UserProductUpdate(BaseModel):
    """Schema for updating user-specific product settings."""

    is_active: bool | None = Field(None, description="Whether user is actively tracking")
    price_change_threshold: float | None = Field(
        None, ge=0, le=100, description="User-specific price threshold %"
    )
    bsr_change_threshold: float | None = Field(
        None, ge=0, le=100, description="User-specific BSR threshold %"
    )
    notes: str | None = Field(None, description="User notes about this product")


class ProductContentUpdate(BaseModel):
    """Schema for updating product content using AI assistance."""

    product_description: str | None = Field(None, description="Enhanced product description")
    features: list[str] | None = Field(None, description="Enhanced product features")
    marketing_copy: str | None = Field(None, description="AI-generated marketing copy")
    seo_keywords: list[str] | None = Field(None, description="SEO-optimized keywords")
    competitor_analysis: str | None = Field(None, description="Competitor analysis notes")


class ProductOut(BaseModel):
    """Schema for product response."""

    id: UUID
    asin: str
    title: str
    brand: str | None
    category: str | None
    small_category: str | None
    url: str
    image_url: str | None
    is_active: bool
    track_frequency: str
    price_change_threshold: float
    bsr_change_threshold: float
    bsr_category_link: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    """Schema for product list response with latest snapshot data."""

    # Product basic info
    id: UUID
    asin: str
    title: str
    brand: str | None
    category: str | None
    url: str
    image_url: str | None
    is_active: bool
    created_at: datetime

    # Latest snapshot data (from most recent scrape)
    price: Decimal | None = None
    original_price: Decimal | None = None
    currency: str = "USD"
    discount_percentage: float | None = None
    bsr_main_category: int | None = None
    rating: float | None = None
    review_count: int = 0
    in_stock: bool = True
    stock_status: str | None = None
    is_prime: bool = False
    scraped_at: datetime | None = None

    # Alert statistics
    unread_alerts_count: int = 0

    model_config = {"from_attributes": True}


class SnapshotOut(BaseModel):
    """Schema for product snapshot response."""

    id: UUID
    product_id: UUID
    price: Decimal | None
    original_price: Decimal | None
    buybox_price: Decimal | None
    currency: str  # Non-nullable in database, default="USD"
    discount_percentage: float | None
    bsr_main_category: int | None
    bsr_small_category: int | None
    main_category_name: str | None
    small_category_name: str | None
    rating: float | None
    review_count: int
    in_stock: bool
    stock_quantity: int | None
    seller_name: str | None
    seller_id: str | None
    seller_store_url: str | None
    is_amazon_seller: bool
    is_fba: bool
    fulfilled_by: str | None
    coupon_available: bool
    coupon_text: str | None
    is_deal: bool
    deal_type: str | None
    is_prime: bool
    has_amazons_choice: bool
    amazons_choice_keywords: dict[str, Any] | None
    past_sales: str | None
    delivery_message: str | None
    product_type: str | None
    is_used: bool
    stock_status: str | None
    scraped_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    """Schema for alert response."""

    id: UUID
    alert_type: str
    severity: str
    title: str
    message: str
    old_value: str | None
    new_value: str | None
    change_percentage: float | None
    is_read: bool
    is_dismissed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductDetailOut(BaseModel):
    """Schema for detailed product response with latest snapshot."""

    id: UUID
    asin: str
    title: str
    brand: str | None
    category: str | None
    small_category: str | None
    url: str
    image_url: str | None
    is_active: bool
    track_frequency: str
    price_change_threshold: float
    bsr_change_threshold: float
    bsr_category_link: str | None
    created_at: datetime
    updated_at: datetime
    latest_snapshot: SnapshotOut | None
    unread_alerts_count: int
    product_description: str | None

    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    """Schema for review response."""

    id: UUID
    review_id: str
    title: str
    text: str
    rating: float
    verified_purchase: bool
    helpful_count: int
    review_date: datetime
    reviewer_name: str | None
    reviewer_id: str | None
    is_vine_voice: bool
    images: list[str] | None
    variant_info: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BestsellerSnapshotOut(BaseModel):
    """Schema for bestseller snapshot response."""

    id: UUID
    category_name: str
    category_url: str
    category_id: str | None
    snapshot_date: datetime
    total_products_scraped: int
    bestsellers: list[dict[str, Any]]
    product_rank: int | None = None  # Product's rank in this category
    top_10: list[dict[str, Any]] | None = None  # Top 10 products

    model_config = {"from_attributes": True}
