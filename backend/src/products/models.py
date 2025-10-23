"""Product models using SQLAlchemy."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BaseModel
from core.utils import now

if TYPE_CHECKING:
    from alert.models import Alert
    from notification.models import Notification
    from optimization.models import Suggestion
    from users.models import User


class Product(BaseModel):
    """Product model to track Amazon products.

    Supports tracking up to 1000+ products with daily snapshots.
    """

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("asin", "marketplace", name="uq_product_asin_marketplace"),
        Index("idx_products_asin", "asin"),
        Index("idx_products_marketplace", "marketplace"),
        Index("idx_products_asin_marketplace", "asin", "marketplace"),
        Index("idx_products_unlisted", "is_unlisted", "unlisted_at"),
        Index("idx_products_created_by", "created_by_id"),
    )

    # Basic product information
    asin: Mapped[str] = mapped_column(String(10), nullable=False, comment="Amazon ASIN")
    marketplace: Mapped[str] = mapped_column(
        String(10),
        default="com",
        nullable=False,
        comment="Amazon marketplace (com, co.uk, de, fr, etc.)",
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="Product title")
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="Brand name")
    manufacturer: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Manufacturer name"
    )
    category: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Main category"
    )
    small_category: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Small/sub category"
    )

    # BSR (Best Seller Rank) information
    bsr_category_link: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Link to main category BSR page"
    )
    bsr_subcategory_link: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Link to subcategory BSR page"
    )

    # Amazon's Choice and badges
    amazons_choice_keywords: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="List of keywords for which this is Amazon's Choice",
    )
    has_amazons_choice: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether product has Amazon's Choice badge",
    )

    # Product specifications
    product_dimensions: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Product dimensions (length, width, height, weight)",
    )
    item_weight: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Item weight (e.g., '10.49 pounds')"
    )
    model_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Manufacturer model number"
    )

    # Variations information
    has_variations: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether product has variations (size, color, etc.)",
    )
    variation_types: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Types of variations available (e.g., ['size_name', 'color_name'])",
    )
    total_variations: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total number of product variations"
    )

    # Product URLs and images
    url: Mapped[str] = mapped_column(String(1000), nullable=False, comment="Amazon product URL")
    image_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, comment="Main product image URL"
    )
    seller_store_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, comment="Seller's Amazon store URL"
    )

    # Product content
    product_description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Full product description"
    )
    features: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="List of product features/bullet points"
    )
    product_overview: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Key product overview attributes (e.g., mounting type)",
    )
    technical_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="Technical specifications"
    )

    # Product rating (latest from snapshots)
    rating: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Current average rating (0-5)"
    )
    review_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Total number of reviews"
    )

    # Denormalized fields from latest snapshot (for performance)
    # These fields are cached from the most recent ProductSnapshot
    current_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Latest price from most recent snapshot",
    )
    original_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Latest original price (before discount)",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="Currency code (USD, GBP, EUR, etc.)",
    )
    discount_percentage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Current discount percentage",
    )
    current_bsr: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Latest Best Seller Rank in main category",
    )
    bsr_category_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="BSR main category name",
    )
    in_stock: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether product is currently in stock",
    )
    stock_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Detailed stock status text",
    )
    is_prime: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether Prime shipping is available",
    )
    seller_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Current seller name",
    )
    is_amazon_seller: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether sold by Amazon",
    )
    is_fba: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether Fulfilled by Amazon (FBA)",
    )
    last_snapshot_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the last snapshot that updated these fields",
    )

    # Tracking settings
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether to actively track this product",
    )
    track_frequency: Mapped[str] = mapped_column(
        String(20),
        default="daily",
        nullable=False,
        comment="Tracking frequency: daily, hourly",
    )

    # Alert thresholds (percentage)
    price_change_threshold: Mapped[float] = mapped_column(
        Float,
        default=10.0,
        nullable=False,
        comment="Alert when price changes more than this percentage",
    )
    bsr_change_threshold: Mapped[float] = mapped_column(
        Float,
        default=30.0,
        nullable=False,
        comment="Alert when BSR changes more than this percentage",
    )

    # Product source (who created/imported this product)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who first imported/created this product record",
    )

    # Product type flags
    is_competitor: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a competitor product (from bestseller scraping)",
    )
    is_unlisted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this product is no longer available on Amazon (404 error)",
    )
    unlisted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when product was marked as unlisted",
    )

    # Relationships
    snapshots: Mapped[list[ProductSnapshot]] = relationship(
        "ProductSnapshot",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductSnapshot.scraped_at.desc()",
    )
    alerts: Mapped[list[Alert]] = relationship(
        "Alert",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list[Review]] = relationship(
        "Review",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    owners: Mapped[list[UserProduct]] = relationship(
        "UserProduct",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    suggestions: Mapped[list[Suggestion]] = relationship(
        "Suggestion",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, asin={self.asin}, marketplace={self.marketplace})>"


class ProductSnapshot(BaseModel):
    """Daily snapshot of Amazon product data.

    Stores time-series data for tracking changes in:
    - Price (current, original, Buy Box)
    - BSR (Best Sellers Rank) in main and small categories
    - Ratings and review counts
    - Stock availability
    """

    __tablename__ = "product_snapshots"
    __table_args__ = (
        Index("idx_snapshot_product_id", "product_id"),
        Index("idx_snapshot_scraped_at", "scraped_at"),
        Index("idx_snapshot_product_scraped", "product_id", "scraped_at"),
    )

    # Foreign key to product
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="Product this snapshot belongs to",
    )

    # Scraping metadata
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now,
        nullable=False,
        comment="When this data was scraped",
    )

    # Price tracking
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Current product price"
    )
    original_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Original/list price"
    )
    buybox_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Buy Box price (may differ from product price)",
    )
    currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False, comment="Currency code"
    )

    # Discount calculation
    discount_percentage: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Discount % if applicable"
    )

    # BSR (Best Sellers Rank) tracking
    bsr_main_category: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="BSR in main category"
    )
    bsr_small_category: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="BSR in small/sub category"
    )
    main_category_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    small_category_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Ratings & Reviews
    rating: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Average rating (0-5)"
    )
    review_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total number of reviews"
    )

    # Availability
    in_stock: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Product availability"
    )
    stock_quantity: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Estimated stock quantity"
    )
    stock_status: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Stock status text"
    )

    # Seller information
    seller_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Current seller name"
    )
    seller_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Amazon seller ID"
    )
    seller_store_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, comment="Seller's store URL at snapshot time"
    )
    is_amazon_seller: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Sold by Amazon"
    )
    is_fba: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Fulfilled by Amazon"
    )
    fulfilled_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Fulfillment provider name"
    )

    # Additional metrics
    coupon_text: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Coupon details if any"
    )
    coupon_available: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Has active coupon"
    )
    deal_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Deal type (Lightning Deal, etc.)"
    )
    is_deal: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Currently on deal"
    )
    is_prime: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Prime eligible"
    )

    # Amazon's Choice tracking
    amazons_choice_keywords: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Keywords for which this is Amazon's Choice at snapshot time",
    )
    has_amazons_choice: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether product had Amazon's Choice badge at snapshot time",
    )

    # Sales and popularity indicators
    past_sales: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Past sales indicator (e.g., '10K+ bought in past month')",
    )

    # Delivery information
    delivery_message: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Delivery time estimate"
    )

    # Product type and classification
    product_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Product type (e.g., 'product_detail')"
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether product is used/refurbished",
    )

    # Category averages (for comparison charts)
    category_avg_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Category average price"
    )
    category_avg_rating: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Category average rating"
    )
    category_avg_reviews: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Category average review count"
    )

    # Relationships
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="snapshots",
    )

    def __repr__(self) -> str:
        return f"<ProductSnapshot(id={self.id}, product_id={self.product_id}, scraped_at={self.scraped_at})>"

    def calculate_price_change_percentage(self, previous_price: Decimal | None) -> float | None:
        """Calculate price change percentage compared to a previous price."""
        if self.price is None or previous_price is None or previous_price == 0:
            return None
        change = ((self.price - previous_price) / previous_price) * 100
        return float(change)


class UserProduct(BaseModel):
    """Many-to-many relationship between users and products.

    Tracks which users are monitoring which products, with individual settings.
    """

    __tablename__ = "user_products"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product"),
        Index("idx_user_products_user_id", "user_id"),
        Index("idx_user_products_product_id", "product_id"),
    )

    # Relationships
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    claimed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now,
        nullable=False,
        comment="When the user started tracking this product",
    )
    # User-specific settings
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether user is actively tracking this product",
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is the user's primary product",
    )
    price_change_threshold: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="User-specific price alert threshold"
    )
    bsr_change_threshold: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="User-specific BSR alert threshold"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="User notes about this product"
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="user_products",
    )
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="owners",
    )

    def __repr__(self) -> str:
        return f"<UserProduct(user_id={self.user_id}, product_id={self.product_id})>"


class Review(BaseModel):
    """Product review from Amazon."""

    __tablename__ = "reviews"
    __table_args__ = (
        Index("idx_reviews_product_id", "product_id"),
        Index("idx_reviews_review_date", "review_date"),
    )

    # Foreign key
    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Review data
    review_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, comment="Amazon review ID"
    )
    reviewer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False, comment="Review rating (1-5)")
    title: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="Review title")
    text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Review text/body")
    review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="reviews",
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, product_id={self.product_id}, rating={self.rating})>"


class Category(BaseModel):
    """Amazon product category hierarchy."""

    __tablename__ = "categories"
    __table_args__ = (
        Index("idx_categories_marketplace", "marketplace"),
        Index("idx_categories_parent_id", "parent_id"),
        UniqueConstraint("category_id", "marketplace", name="uq_category_marketplace"),
    )

    # Category identification
    category_id: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="Amazon category ID"
    )
    marketplace: Mapped[str] = mapped_column(
        String(10), default="com", nullable=False, comment="Amazon marketplace"
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="Category name")
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="Category URL")

    # Hierarchy
    parent_id: Mapped[UUID | None] = mapped_column(
        UUID,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent category",
    )
    level: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Category depth level"
    )

    # Metadata
    product_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    parent: Mapped[Category | None] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
    )
    children: Mapped[list[Category]] = relationship(
        "Category",
        back_populates="parent",
    )
    bestseller_snapshots: Mapped[list[BestsellerSnapshot]] = relationship(
        "BestsellerSnapshot",
        back_populates="category",
        cascade="all, delete-orphan",
    )
    metrics: Mapped[list[CategoryMetric]] = relationship(
        "CategoryMetric",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name}, marketplace={self.marketplace})>"

    def parse_category_id(self) -> list[str]:
        """Parse the category_id into its hierarchical components."""
        # try pattern https://www.amazon.co.uk/gp/bestsellers/videogames/ref=pd_zg_ts_videogames
        return self.url.split("/gp/bestsellers/")[1].split("/")[0]


class BestsellerSnapshot(BaseModel):
    """Snapshot of bestseller rankings in a category."""

    __tablename__ = "bestseller_snapshots"
    __table_args__ = (
        Index("idx_bestseller_category_id", "category_id"),
        Index("idx_bestseller_scraped_at", "scraped_at"),
    )

    # Foreign key
    category_id: Mapped[UUID] = mapped_column(
        UUID,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Snapshot data
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When this data was scraped",
    )
    rank: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Bestseller rank in category"
    )
    asin: Mapped[str] = mapped_column(String(10), nullable=False, comment="Product ASIN")
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    category: Mapped[Category] = relationship(
        "Category",
        back_populates="bestseller_snapshots",
    )

    def __repr__(self) -> str:
        return (
            f"<BestsellerSnapshot(id={self.id}, category_id={self.category_id}, rank={self.rank})>"
        )


class CategoryMetric(BaseModel):
    """Aggregated metrics for product categories.

    Stores daily averages and statistics for entire product categories
    to enable comparison against category benchmarks in charts.
    """

    __tablename__ = "category_metrics"
    __table_args__ = (
        Index("idx_category_metrics_category_id", "category_id"),
        Index("idx_category_metrics_recorded_at", "recorded_at"),
        Index("idx_category_metrics_category_recorded", "category_id", "recorded_at"),
    )

    # Foreign key to category
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        comment="Category this metric belongs to",
    )

    # Category level
    category_level: Mapped[str] = mapped_column(
        String(20),
        default="main",
        nullable=False,
        comment="Category level: 'main' or 'subcategory'",
    )

    # Timestamp
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now,
        comment="When these metrics were recorded",
    )

    # Aggregated price metrics
    avg_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Average price in category"
    )
    median_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Median price in category"
    )
    min_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Minimum price in category"
    )
    max_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Maximum price in category"
    )

    # Aggregated BSR metrics
    avg_bsr: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Average best seller rank"
    )
    median_bsr: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Median best seller rank"
    )

    # Aggregated review metrics
    avg_rating: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Average rating in category"
    )
    avg_review_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Average number of reviews"
    )

    # Sample size
    product_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of products in this category",
    )

    # Relationships
    category: Mapped[Category] = relationship(
        "Category",
        back_populates="metrics",
    )

    def __repr__(self) -> str:
        return f"<CategoryMetric(id={self.id}, category_id={self.category_id}, recorded_at={self.recorded_at})>"
