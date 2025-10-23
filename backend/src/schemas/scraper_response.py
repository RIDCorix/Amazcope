"""Pydantic schemas for normalized scraper responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProductDimensionDetail(BaseModel):
    """Product dimension information."""

    name: str
    value: str


class ProductOverviewDetail(BaseModel):
    """Product overview detail."""

    name: str
    value: str


class ProductTechnicalDetail(BaseModel):
    """Product technical specification detail."""

    name: str
    value: str


class NormalizedProductResponse(BaseModel):
    """Normalized product data from scraper service.

    This is the standardized response format from apify_service.scrape_product().
    All fields from various scraper formats are normalized to this schema.
    """

    # Basic info
    asin: str = Field(..., description="Amazon Standard Identification Number")
    title: str = Field(..., description="Product title")
    brand: str | None = Field(None, description="Product brand name")
    manufacturer: str | None = Field(None, description="Product manufacturer")
    url: str = Field(..., description="Amazon product URL")
    image_url: str | None = Field(None, description="Primary product image URL")

    # Product content
    product_description: str | None = Field(None, description="Full product description")
    features: list[str] | None = Field(None, description="Product feature bullet points")
    product_overview: list[ProductOverviewDetail] | None = Field(
        None, description="Product overview details"
    )
    technical_details: list[ProductTechnicalDetail] | None = Field(
        None, description="Technical specifications"
    )

    # Product specifications
    item_weight: str | None = Field(None, description="Item weight (e.g., '1.5 pounds')")
    model_number: str | None = Field(None, description="Manufacturer model number")
    product_dimensions: dict[str, Any] | None = Field(
        None, description="Product dimensions mapping"
    )

    # Price
    price: float | None = Field(None, description="Current selling price")
    original_price: float | None = Field(None, description="Original/retail price")
    buybox_price: float | None = Field(None, description="Buy box price for used items")
    currency: str = Field(default="USD", description="Currency code")
    discount_percentage: float | None = Field(None, description="Discount percentage (0-100)")

    # BSR (Best Seller Rank)
    bsr_main_category: int | None = Field(None, description="Main category BSR rank")
    bsr_small_category: int | None = Field(None, description="Subcategory BSR rank")
    main_category_name: str | None = Field(None, description="Main category name")
    small_category_name: str | None = Field(None, description="Subcategory name")
    bsr_category_link: str | None = Field(None, description="Main category BSR link")
    bsr_subcategory_link: str | None = Field(None, description="Subcategory BSR link")

    # Ratings & Reviews
    rating: float | None = Field(None, description="Average rating (0-5)")
    review_count: int = Field(default=0, description="Total number of reviews")
    product_rating_text: str | None = Field(
        None, description="Full rating text (e.g., '4.7 out of 5 stars')"
    )

    # Availability
    in_stock: bool = Field(default=False, description="Whether product is in stock")
    stock_quantity: int | None = Field(None, description="Available stock quantity")
    stock_status: str | None = Field(
        None, description="Stock status text (e.g., 'In Stock', 'Only 3 left')"
    )

    # Seller info
    seller_name: str | None = Field(None, description="Seller name")
    seller_id: str | None = Field(None, description="Seller ID")
    seller_store_url: str | None = Field(None, description="Seller store URL")
    is_amazon_seller: bool = Field(default=False, description="Whether Amazon is the seller")
    is_fba: bool = Field(default=False, description="Whether product is fulfilled by Amazon (FBA)")
    fulfilled_by: str | None = Field(None, description="Fulfillment provider")

    # Amazon's Choice
    amazons_choice_keywords: list[str] | None = Field(
        None, description="Keywords for which this product is Amazon's Choice"
    )
    has_amazons_choice: bool = Field(
        default=False, description="Whether product has Amazon's Choice badge"
    )

    # Variations
    has_variations: bool = Field(default=False, description="Whether product has variations")
    variation_types: list[str] | None = Field(
        None, description="Types of variations available (e.g., ['Color', 'Size'])"
    )
    total_variations: int = Field(default=0, description="Total number of variations")
    dimensions_map: dict[str, Any] | None = Field(None, description="Variation dimensions mapping")
    variation_values: dict[str, Any] | None = Field(
        None, description="Variation values by type (e.g., {'Color': ['Red', 'Blue']})"
    )

    # Additional
    coupon_text: str | None = Field(None, description="Coupon information text")
    deal_type: str | None = Field(None, description="Type of deal (e.g., 'deal', 'lightning')")
    is_deal: bool = Field(default=False, description="Whether product is on deal")
    prime: bool = Field(default=False, description="Whether product has Prime shipping")
    is_prime: bool = Field(default=False, description="Whether product has Prime shipping")
    is_used: bool = Field(default=False, description="Whether product is used/refurbished")
    past_sales: str | None = Field(
        None, description="Past sales indicator (e.g., '10K+ bought in past month')"
    )
    delivery_message: str | None = Field(
        None, description="Delivery message (e.g., 'FREE delivery Tomorrow')"
    )
    product_type: str | None = Field(None, description="Product type classification")
    input_url: str | None = Field(None, description="Original input URL used for scraping")

    @property
    def category_url(self) -> str | None:
        """Construct category URL from BSR category link if available."""
        if self.bsr_category_link:
            return self.bsr_category_link
        domain = self.url.split("//")[1].split("/")[0] if self.url else "www.amazon.com"
        return f"https://{domain}/gp/bestsellers/videogames/ref=pd_zg_ts_videogames"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asin": "B07XJ8C8F5",
                "title": "VIVO Dual Monitor Desk Mount",
                "brand": "VIVO",
                "manufacturer": "VIVO",
                "url": "https://www.amazon.com/dp/B07XJ8C8F5",
                "image_url": "https://m.media-amazon.com/images/I/71abc123.jpg",
                "product_description": "Full product description here...",
                "features": [
                    'Fits most monitors 13" to 27"',
                    "Supports up to 22 lbs per arm",
                ],
                "price": 45.99,
                "original_price": 59.99,
                "currency": "USD",
                "discount_percentage": 23.34,
                "bsr_main_category": 74,
                "main_category_name": "Computer Monitor Arms",
                "bsr_category_link": "https://www.amazon.com/gp/bestsellers/...",
                "rating": 4.7,
                "review_count": 15234,
                "in_stock": True,
                "stock_status": "In Stock",
                "seller_name": "Amazon.com",
                "is_amazon_seller": True,
                "is_fba": True,
                "amazons_choice_keywords": ["monitor mount", "dual monitor stand"],
                "has_amazons_choice": True,
                "has_variations": True,
                "variation_types": ["Color"],
                "total_variations": 2,
                "is_deal": False,
                "prime": True,
                "past_sales": "10K+ bought in past month",
                "delivery_message": "FREE delivery Tomorrow",
            }
        }
    )


class BatchProductResponse(BaseModel):
    """Response for batch product scraping.

    Maps ASIN to normalized product data for all successful scrapes.
    """

    products: dict[str, NormalizedProductResponse] = Field(
        ..., description="Mapping of ASIN to product data"
    )
    total_requested: int = Field(..., description="Total number of ASINs requested")
    total_successful: int = Field(..., description="Total number of successful scrapes")
    total_failed: int = Field(..., description="Total number of failed scrapes")
    success_rate: float = Field(..., description="Success rate percentage (0-100)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "products": {
                    "B07XJ8C8F5": {
                        "asin": "B07XJ8C8F5",
                        "title": "VIVO Dual Monitor Desk Mount",
                        "price": 45.99,
                        # ... other fields
                    }
                },
                "total_requested": 10,
                "total_successful": 9,
                "total_failed": 1,
                "success_rate": 90.0,
            }
        }
    )
