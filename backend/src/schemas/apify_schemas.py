"""Pydantic schemas for Apify API responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PriceInfo(BaseModel):
    """Price information for a product."""

    retail_price: float | None = Field(None, alias="retailPrice")
    price: float | None = None
    price_range: str | None = Field(None, alias="priceRange")
    shipping_price: float | None = Field(None, alias="shippingPrice")
    price_saving: str | None = Field(None, alias="priceSaving")


class ProductDetail(BaseModel):
    """Product detail key-value pair."""

    name: str
    value: str


class Review(BaseModel):
    """Product review."""

    text: str
    date: str
    rating: str
    title: str | None = None
    user_name: str = Field(alias="userName")
    url: str
    image_url_list: list[str] = Field(default_factory=list, alias="imageUrlList")
    variation_list: list[str] = Field(default_factory=list, alias="variationList")
    review_id: str = Field(alias="reviewId")
    locale: dict[str, Any] | None = None


class Variation(BaseModel):
    """Product variation."""

    variation_name: str = Field(alias="variationName")
    values: list[dict[str, Any]] = Field(default_factory=list)


class Category(BaseModel):
    """Product category."""

    name: str
    url: str
    node: str


class BuyBoxUsed(BaseModel):
    """Used buy box information."""

    condition: str | None = None
    package_condition: str | None = Field(None, alias="packageCondition")
    sold_by: str | None = Field(None, alias="soldBy")
    fulfilled_by: str | None = Field(None, alias="fulfilledBy")
    seller_id: str | None = Field(None, alias="sellerId")
    warehouse_availability: str | None = Field(None, alias="warehouseAvailability")
    retail_price: float | None = Field(None, alias="retailPrice")
    price: float | None = None
    price_shipping_information: str | None = Field(None, alias="priceShippingInformation")
    price_saving: str | None = Field(None, alias="priceSaving")


class ReviewInsightFeature(BaseModel):
    """Review insight feature aspect."""

    name: str
    feature_mention_count: int = Field(alias="featureMentionCount")
    feature_mention_positive_count: int = Field(alias="featureMentionPositiveCount")
    feature_mention_negative_count: int = Field(alias="featureMentionNegativeCount")
    key_facts: str = Field(alias="keyFacts")
    summary: str
    sentiment: str
    review_snippets: list[dict[str, Any]] = Field(default_factory=list, alias="reviewSnippets")


class BestSellerRank(BaseModel):
    """Best Seller Rank information."""

    rank: str
    category_name: str = Field(alias="categoryName")
    link: str

    model_config = ConfigDict(populate_by_name=True)


class ReviewInsights(BaseModel):
    """AI-generated review insights."""

    summary: str
    banner: str
    feature_aspects: list[ReviewInsightFeature] = Field(
        default_factory=list, alias="featureAspects"
    )


class BestsellerPrice(BaseModel):
    """Price information for bestseller product."""

    value: float
    currency: str


class BestsellerItem(BaseModel):
    """Single bestseller item from Apify scraper."""

    position: int
    thumbnail_url: str = Field(alias="thumbnailUrl")
    name: str
    price: BestsellerPrice | None
    category_name: str = Field(alias="categoryName")
    url: str

    model_config = ConfigDict(populate_by_name=True)


class ApifyProductResponse(BaseModel):
    """Response from Apify product scraper."""

    status_code: int = Field(alias="statusCode")
    status_message: str = Field(alias="statusMessage")
    url: str
    title: str | None = None
    manufacturer: str | None = None
    count_review: int = Field(0, alias="countReview")
    product_rating: str | None = Field(None, alias="productRating")
    asin: str | None = None
    sold_by: str | None = Field(None, alias="soldBy")
    fulfilled_by: str | None = Field(None, alias="fulfilledBy")
    seller_id: str | None = Field(None, alias="sellerId")
    warehouse_availability: str | None = Field(None, alias="warehouseAvailability")
    retail_price: float | None = Field(None, alias="retailPrice")
    price: float | None = None
    price_range: str | None = Field(None, alias="priceRange")
    shipping_price: float | None = Field(None, alias="shippingPrice")
    price_shipping_information: str | None = Field(None, alias="priceShippingInformation")
    price_saving: str | None = Field(None, alias="priceSaving")
    features: list[str] = Field(default_factory=list)
    image_url_list: list[str] = Field(default_factory=list, alias="imageUrlList")
    videoe_url_list: list[str] = Field(default_factory=list, alias="videoeUrlList")
    product_description: str | None = Field(None, alias="productDescription")
    product_details: list[ProductDetail] | None = Field(
        default_factory=list, alias="productDetails"
    )
    minimal_quantity: str | None = Field(None, alias="minimalQuantity")
    reviews: list[Review] = Field(default_factory=list)
    product_specification: list[dict[str, Any]] = Field(
        default_factory=list, alias="productSpecification"
    )
    main_image: dict[str, Any] | None = Field(None, alias="mainImage")
    variations: list[Variation] = Field(default_factory=list)
    book_variations: list[dict[str, Any]] = Field(default_factory=list, alias="bookVariations")
    categories_extended: list[Category] = Field(default_factory=list, alias="categoriesExtended")
    delivery_message: str | None = Field(None, alias="deliveryMessage")
    important_information: list[dict[str, Any]] = Field(
        default_factory=list, alias="importantInformation"
    )
    buy_box_used: BuyBoxUsed | None = Field(None, alias="buyBoxUsed")
    about_product: list[ProductDetail] = Field(default_factory=list, alias="aboutProduct")
    global_reviews: list[Review] = Field(default_factory=list, alias="globalReviews")
    deal: bool = False
    prime: bool = False
    used: bool = False
    past_sales: str | None = Field(None, alias="pastSales")
    review_insights: ReviewInsights | None = Field(None, alias="reviewInsights")
    best_sellers_rank: list[BestSellerRank] = Field(default_factory=list, alias="bestSellersRank")
    input_url: str | None = Field(None, alias="inputUrl")
    seller: dict[str, Any] | None = None
    amazons_choice_keywords: list[str] = Field(default_factory=list, alias="amazonsChoiceKeywords")
    product_overview: list[ProductDetail] = Field(default_factory=list, alias="productOverview")
    technical_details: list[ProductDetail] = Field(default_factory=list, alias="technicalDetails")
    dimensions: dict[str, Any] = Field(default_factory=dict)
    variation_values: dict[str, Any] = Field(default_factory=dict, alias="variationValues")
    type: str | None = None

    model_config = ConfigDict(populate_by_name=True)
