"""Pydantic schemas for product metrics API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductMetricBase(BaseModel):
    """Base schema for product metrics."""

    recorded_at: datetime
    price: Decimal | None = None
    original_price: Decimal | None = None
    buybox_price: Decimal | None = None
    discount_percentage: float | None = None
    bsr_main_category: int | None = None
    bsr_small_category: int | None = None
    rating: float | None = None
    review_count: int = 0
    in_stock: bool = True
    stock_status: str | None = None
    seller_name: str | None = None
    is_amazon_seller: bool = False
    is_fba: bool = False
    is_deal: bool = False
    is_prime: bool = False
    coupon_available: bool = False
    coupon_text: str | None = None


class ProductMetricCreate(ProductMetricBase):
    """Schema for creating a new product metric."""

    product_id: UUID


class ProductMetricResponse(ProductMetricBase):
    """Schema for product metric response."""

    id: UUID
    product_id: UUID
    category_avg_price: Decimal | None = None
    category_avg_rating: float | None = None
    category_avg_reviews: int | None = None
    scrape_successful: bool = True
    scrape_error: str | None = None

    model_config = {"from_attributes": True}


class MetricDataPoint(BaseModel):
    """Single data point for chart visualization."""

    date: datetime
    value: float | None


class PriceTrendData(BaseModel):
    """Price trend data for charts."""

    date: datetime
    price: float | None
    buybox_price: float | None
    original_price: float | None
    category_avg_price: float | None = None


class BSRTrendData(BaseModel):
    """BSR trend data for charts."""

    date: datetime
    bsr_main: int | None
    bsr_small: int | None


class ReviewTrendData(BaseModel):
    """Review trend data for charts."""

    date: datetime
    rating: float | None
    review_count: int | None
    category_avg_rating: float | None = None
    category_avg_reviews: int | None = None


class MetricComparisonRequest(BaseModel):
    """Request schema for comparing product metrics."""

    product_ids: list[UUID] = Field(..., min_length=1, max_length=10)
    metric_type: str = Field(
        ...,
        description="Type of metric: 'price', 'bsr', 'rating', 'reviews'",
        pattern="^(price|bsr|rating|reviews)$",
    )
    days: int = Field(default=30, ge=1, le=365)


class ProductMetricTrend(BaseModel):
    """Trend data for a single product."""

    product_id: UUID
    product_title: str
    product_asin: str
    data_points: list[PriceTrendData] | list[BSRTrendData] | list[ReviewTrendData]


class MetricComparisonResponse(BaseModel):
    """Response schema for metric comparison."""

    metric_type: str
    start_date: datetime
    end_date: datetime
    products: list[ProductMetricTrend]
    category_average: list[MetricDataPoint] | None = None


class CategoryTrendRequest(BaseModel):
    """Request schema for category trend data."""

    category_name: str
    days: int = Field(default=30, ge=1, le=365)


class MetricsSummary(BaseModel):
    """Summary statistics for a product."""

    product_id: UUID
    current_price: Decimal | None
    price_change_7d: float | None
    price_change_30d: float | None
    current_bsr: int | None
    bsr_change_7d: float | None
    bsr_change_30d: float | None
    current_rating: float | None
    rating_change_7d: float | None
    rating_change_30d: float | None
    review_count: int
    review_growth_7d: int | None
    review_growth_30d: int | None
    last_updated: datetime
