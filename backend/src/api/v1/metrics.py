"""API endpoints for product metrics tracking and comparison."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, get_current_user
from products.models import ProductSnapshot, UserProduct
from schemas.metrics import (
    CategoryTrendRequest,
    MetricComparisonRequest,
    MetricComparisonResponse,
    MetricDataPoint,
    MetricsSummary,
    ProductMetricResponse,
)
from services.metric_field_registry import MetricFieldRegistry
from services.metrics_service import MetricsAggregationService
from users.models import User

router = APIRouter()


@router.get("/products/{product_id}/summary", response_model=MetricsSummary)
async def get_product_metrics_summary(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get metrics summary for a product with 7-day and 30-day changes.

    Returns current values and percentage changes for:
    - Price
    - BSR (Best Seller Rank)
    - Rating
    - Review count

    **Example Response:**
    ```json
    {
        "product_id": 123,
        "current_price": 29.99,
        "price_change_7d": -5.2,
        "price_change_30d": -12.1,
        "current_bsr": 15234,
        "bsr_change_7d": 8.5,
        "bsr_change_30d": -3.2,
        "current_rating": 4.5,
        "rating_change_7d": 0.1,
        "rating_change_30d": 0.3,
        "review_count": 1543,
        "review_growth_7d": 23,
        "review_growth_30d": 87,
        "last_updated": "2025-01-18T10:30:00Z"
    }
    ```
    """
    # Verify product ownership
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == current_user.id,
            UserProduct.product_id == product_id,
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get summary
    summary = await MetricsAggregationService.get_metrics_summary(db, product_id)
    if not summary:
        raise HTTPException(status_code=404, detail="No metrics data available for this product")

    return summary


@router.get("/products/{product_id}/metrics", response_model=list[ProductMetricResponse])
async def get_product_metrics(
    product_id: UUID,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to retrieve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get all metrics for a product within a date range.

    **Parameters:**
    - **days**: Number of days to retrieve (1-365)

    **Returns:** List of all recorded metrics
    """
    # Verify product ownership
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == current_user.id,
            UserProduct.product_id == product_id,
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    start_date = datetime.now(UTC) - timedelta(days=days)
    result = await db.execute(
        select(ProductSnapshot)
        .where(
            ProductSnapshot.product_id == product_id,
            ProductSnapshot.scraped_at >= start_date,
        )
        .order_by(ProductSnapshot.scraped_at)
    )
    metrics = result.scalars().all()

    return [ProductMetricResponse.model_validate(m) for m in metrics]


@router.post("/compare", response_model=MetricComparisonResponse)
async def compare_products(
    request: MetricComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Compare metrics for multiple products with optional category average overlay.

    **Request Body:**
    ```json
    {
        "product_ids": [123, 456, 789],
        "metric_type": "price",
        "days": 30
    }
    ```

    **Metric Types:**
    - `price`: Price, Buy Box, and Original Price comparison
    - `bsr`: Best Seller Rank comparison
    - `rating`: Rating and review count comparison
    - `reviews`: Review count growth

    **Response:** Time-series data for all products plus category average

    **Example Response:**
    ```json
    {
        "metric_type": "price",
        "start_date": "2024-12-19T00:00:00Z",
        "end_date": "2025-01-18T00:00:00Z",
        "products": [
            {
                "product_id": 123,
                "product_title": "Product A",
                "product_asin": "B01ABCD123",
                "data_points": [
                    {
                        "date": "2024-12-19T00:00:00Z",
                        "price": 29.99,
                        "buybox_price": 29.99,
                        "original_price": 39.99
                    }
                ]
            }
        ],
        "category_average": [
            {
                "date": "2024-12-19T00:00:00Z",
                "value": 32.50
            }
        ]
    }
    ```
    """
    # Verify all products belong to user
    for product_id in request.product_ids:
        result = await db.execute(
            select(UserProduct).where(
                UserProduct.user_id == current_user.id,
                UserProduct.product_id == product_id,
            )
        )
        ownership = result.scalar_one_or_none()
        if not ownership:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found or access denied",
            )

    # Get comparison data
    comparison = await MetricsAggregationService.get_product_comparison(
        db,
        product_ids=request.product_ids,
        metric_type=request.metric_type,
        days=request.days,
    )

    return comparison


@router.post("/category/trend", response_model=list[MetricDataPoint])
async def get_category_trend(
    request: CategoryTrendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get category average trend data.

    **Request Body:**
    ```json
    {
        "category_name": "Electronics > Smartphones",
        "days": 30
    }
    ```

    **Returns:** Time-series data of category averages
    """
    trend = await MetricsAggregationService.get_category_trend(
        db=db, category_name=request.category_name, days=request.days
    )

    return trend


@router.get("/products/{product_id}/latest", response_model=ProductMetricResponse)
async def get_latest_metric(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get the most recent metric snapshot for a product.

    **Returns:** Latest recorded metric data
    """
    # Verify product ownership
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == current_user.id,
            UserProduct.product_id == product_id,
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(
        select(ProductSnapshot)
        .where(ProductSnapshot.product_id == product_id)
        .order_by(ProductSnapshot.scraped_at.desc())
        .limit(1)
    )
    metric = result.scalar_one_or_none()
    if not metric:
        raise HTTPException(status_code=404, detail="No metrics data available")

    return ProductMetricResponse.model_validate(metric)


# ==================== NEW DYNAMIC FIELD SYSTEM ====================


@router.get("/fields/available")
async def get_available_fields(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get all available metric fields that can be queried.

    **Returns:** Field registry with categories, types, and descriptions

    **Response Structure:**
    ```json
    {
        "categories": {
            "price": [
                {
                    "name": "price",
                    "display_name": "Current Price",
                    "description": "Product's current selling price",
                    "type": "float"
                }
            ],
            "ranking": [...],
            "reviews": [...]
        },
        "total_fields": 15
    }
    ```

    **Use this endpoint to:**
    - Build dynamic UI dropdowns/checkboxes
    - Generate TypeScript types
    - Display field metadata in documentation
    """
    return MetricFieldRegistry.get_field_schema()


@router.get("/products/{product_id}/trends")
async def get_product_trends(
    product_id: UUID,
    fields: list[str] = Query(
        ...,
        description=(
            "Metric fields to retrieve (comma-separated). "
            "Use /fields/available to see all options. "
            "Examples: price,bsr_main,rating"
        ),
    ),
    days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days to retrieve (1-365)",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """🚀 **Dynamic metric trends endpoint** - Query any combination of fields!

    **This single endpoint replaces /price-trend, /bsr-trend, and /review-trend.**

    **Examples:**

    1. **Price tracking:**
       ```
       GET /trends?fields=price&fields=buybox_price&fields=original_price&days=30
       ```

    2. **BSR + Rating combo:**
       ```
       GET /trends?fields=bsr_main&fields=bsr_small&fields=rating&days=90
       ```

    3. **Full dashboard view:**
       ```
       GET /trends?fields=price,bsr_main,rating,review_count,in_stock&days=7
       ```

    **Response Structure:**
    ```json
    {
        "metadata": {
            "price": {
                "display_name": "Current Price",
                "description": "Product's current selling price",
                "type": "float",
                "category": "price"
            },
            "bsr_main": {
                "display_name": "BSR (Main Category)",
                "description": "Best Sellers Rank in main category",
                "type": "int",
                "category": "ranking"
            }
        },
        "data": [
            {
                "date": "2025-01-18T00:00:00Z",
                "price": 29.99,
                "bsr_main": 1234
            },
            {
                "date": "2025-01-17T00:00:00Z",
                "price": 32.99,
                "bsr_main": 1150
            }
        ],
        "total_points": 30
    }
    ```

    **Benefits:**
    - ✅ No new API endpoints needed for new metrics
    - ✅ Frontend can query exactly what it needs
    - ✅ Automatic field validation
    - ✅ Self-documenting with metadata
    - ✅ Type-safe with OpenAPI schema generation

    **Adding New Fields:**
    Just add to `MetricFieldRegistry._fields` dict - no API changes needed!
    """
    # Verify product ownership
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == current_user.id,
            UserProduct.product_id == product_id,
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    # Handle comma-separated field names
    # FastAPI Query with list[str] can receive either:
    # - Repeated params: ?fields=price&fields=bsr_main
    # - Single comma-separated: ?fields=price,bsr_main
    # We need to flatten and split to handle both cases
    field_list: list[str] = []
    for field in fields:
        if "," in field:
            # Split comma-separated values
            field_list.extend(f.strip() for f in field.split(","))
        else:
            field_list.append(field.strip())

    # Validate and get trend data
    try:
        trend_data = await MetricFieldRegistry.get_trend_data(
            db, product_id=product_id, field_names=field_list, days=days
        )
        return trend_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
