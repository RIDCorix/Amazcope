"""Dynamic metric field registry for flexible charting.

This module provides a registry of available metric fields that can be queried
dynamically without creating new API endpoints for each metric.

**Philosophy:**
Instead of creating separate endpoints like /price-trend, /bsr-trend, /review-trend,
we have a single /trends endpoint that accepts field names as parameters.

**Usage:**
```python
# Get price and BSR data
GET /api/v1/metrics/products/123/trends?fields=price,buybox_price,bsr_main&days=30

# Get all review-related metrics
GET /api/v1/metrics/products/123/trends?fields=rating,review_count&days=90
```
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    pass


@dataclass
class MetricField:
    """Definition of a queryable metric field.

    Attributes:
        name: Field identifier (used in API requests)
        display_name: Human-readable name for UI
        description: Field documentation
        extractor: Function to extract value from ProductSnapshot
        field_type: Data type (for validation and type generation)
        category: Grouping category (price, ranking, reviews, etc.)
    """

    name: str
    display_name: str
    description: str
    extractor: Callable[..., Any]
    field_type: str  # 'float', 'int', 'bool', 'string'
    category: str


class MetricFieldRegistry:
    """Registry of all available metric fields for dynamic querying.

    This registry acts as a single source of truth for:
    - Available fields that can be queried
    - Field metadata (type, description, category)
    - Data extraction logic from ProductSnapshot

    **Adding New Fields:**
    Just add a new entry to `_fields` dict. No new API endpoints needed!
    """

    _fields: dict[str, MetricField] = {
        # Price Metrics
        "price": MetricField(
            name="price",
            display_name="Current Price",
            description="Product's current selling price",
            extractor=lambda s: float(s.price) if s.price else None,
            field_type="float",
            category="price",
        ),
        "original_price": MetricField(
            name="original_price",
            display_name="Original Price",
            description="Product's list/MSRP price",
            extractor=lambda s: float(s.original_price) if s.original_price else None,
            field_type="float",
            category="price",
        ),
        "buybox_price": MetricField(
            name="buybox_price",
            display_name="Buy Box Price",
            description="Price shown in Buy Box (may differ from listing price)",
            extractor=lambda s: float(s.buybox_price) if s.buybox_price else None,
            field_type="float",
            category="price",
        ),
        "discount_percentage": MetricField(
            name="discount_percentage",
            display_name="Discount %",
            description="Current discount percentage",
            extractor=lambda s: s.discount_percentage,
            field_type="float",
            category="price",
        ),
        # BSR (Best Sellers Rank) Metrics
        "bsr_main": MetricField(
            name="bsr_main",
            display_name="BSR (Main Category)",
            description="Best Sellers Rank in main category (lower is better)",
            extractor=lambda s: s.bsr_main_category,
            field_type="int",
            category="ranking",
        ),
        "bsr_small": MetricField(
            name="bsr_small",
            display_name="BSR (Subcategory)",
            description="Best Sellers Rank in subcategory (lower is better)",
            extractor=lambda s: s.bsr_small_category,
            field_type="int",
            category="ranking",
        ),
        # Review Metrics
        "rating": MetricField(
            name="rating",
            display_name="Star Rating",
            description="Average customer rating (0-5 stars)",
            extractor=lambda s: s.rating,
            field_type="float",
            category="reviews",
        ),
        "review_count": MetricField(
            name="review_count",
            display_name="Review Count",
            description="Total number of customer reviews",
            extractor=lambda s: s.review_count,
            field_type="int",
            category="reviews",
        ),
        # Availability Metrics
        "in_stock": MetricField(
            name="in_stock",
            display_name="In Stock",
            description="Product availability status",
            extractor=lambda s: s.in_stock,
            field_type="bool",
            category="availability",
        ),
        "stock_quantity": MetricField(
            name="stock_quantity",
            display_name="Stock Quantity",
            description="Estimated stock quantity (if available)",
            extractor=lambda s: s.stock_quantity,
            field_type="int",
            category="availability",
        ),
        # Deal & Prime Metrics
        "is_deal": MetricField(
            name="is_deal",
            display_name="On Deal",
            description="Whether product is currently on a deal",
            extractor=lambda s: s.is_deal,
            field_type="bool",
            category="deals",
        ),
        "is_prime": MetricField(
            name="is_prime",
            display_name="Prime Eligible",
            description="Whether product is Prime eligible",
            extractor=lambda s: s.is_prime,
            field_type="bool",
            category="deals",
        ),
        "has_amazons_choice": MetricField(
            name="has_amazons_choice",
            display_name="Amazon's Choice",
            description="Whether product has Amazon's Choice badge",
            extractor=lambda s: s.has_amazons_choice,
            field_type="bool",
            category="badges",
        ),
        # Seller Metrics
        "is_amazon_seller": MetricField(
            name="is_amazon_seller",
            display_name="Sold by Amazon",
            description="Whether product is sold directly by Amazon",
            extractor=lambda s: s.is_amazon_seller,
            field_type="bool",
            category="seller",
        ),
        "is_fba": MetricField(
            name="is_fba",
            display_name="FBA",
            description="Whether product is Fulfilled by Amazon",
            extractor=lambda s: s.is_fba,
            field_type="bool",
            category="seller",
        ),
    }

    @classmethod
    def get_field(cls, field_name: str) -> MetricField | None:
        """Get field definition by name."""
        return cls._fields.get(field_name)

    @classmethod
    def get_all_fields(cls) -> dict[str, MetricField]:
        """Get all registered fields."""
        return cls._fields.copy()

    @classmethod
    def get_fields_by_category(cls, category: str) -> dict[str, MetricField]:
        """Get all fields in a specific category."""
        return {name: field for name, field in cls._fields.items() if field.category == category}

    @classmethod
    def get_available_field_names(cls) -> list[str]:
        """Get list of all queryable field names."""
        return list(cls._fields.keys())

    @classmethod
    def validate_field_names(cls, field_names: list[str]) -> tuple[bool, list[str]]:
        """Validate that all requested fields exist.

        Returns:
            Tuple of (is_valid, invalid_fields)
        """
        invalid = [name for name in field_names if name not in cls._fields]
        return len(invalid) == 0, invalid

    @classmethod
    async def get_trend_data(
        cls, db: Any, product_id: UUID, field_names: list[str], days: int = 30
    ) -> dict[str, Any]:
        """Get trend data for multiple fields.

        Args:
            db: AsyncSession for database queries
            product_id: Product ID to query
            field_names: List of field names to retrieve
            days: Number of days to go back

        Returns:
            Dictionary with:
            - metadata: Field definitions
            - data: List of data points with date and requested fields

        Example:
        ```json
        {
            "metadata": {
                "price": {"display_name": "Current Price", "type": "float", ...},
                "bsr_main": {"display_name": "BSR (Main Category)", "type": "int", ...}
            },
            "data": [
                {"date": "2025-01-18T00:00:00Z", "price": 29.99, "bsr_main": 1234},
                {"date": "2025-01-17T00:00:00Z", "price": 32.99, "bsr_main": 1150}
            ]
        }
        ```
        """

        from sqlalchemy import select

        from products.models import (
            ProductSnapshot,
        )  # Import here to avoid circular imports

        # Validate fields
        is_valid, invalid = cls.validate_field_names(field_names)
        if not is_valid:
            raise ValueError(f"Invalid field names: {', '.join(invalid)}")

        # Get snapshots
        start_date = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(ProductSnapshot)
            .where(
                ProductSnapshot.product_id == product_id,
                ProductSnapshot.scraped_at >= start_date,
            )
            .order_by(ProductSnapshot.scraped_at)
        )
        result = await db.execute(stmt)
        snapshots = result.scalars().all()

        # Extract data
        data_points = []
        for snapshot in snapshots:
            point: dict[str, Any] = {"date": snapshot.scraped_at.isoformat()}
            for field_name in field_names:
                field = cls._fields[field_name]
                point[field_name] = field.extractor(snapshot)
            data_points.append(point)

        # Build metadata
        metadata = {}
        for field_name in field_names:
            field = cls._fields[field_name]
            metadata[field_name] = {
                "display_name": field.display_name,
                "description": field.description,
                "type": field.field_type,
                "category": field.category,
            }

        return {
            "metadata": metadata,
            "data": data_points,
            "total_points": len(data_points),
        }

    @classmethod
    def get_field_schema(cls) -> dict[str, Any]:
        """Get OpenAPI-compatible schema for all fields.

        Useful for generating TypeScript types and API documentation.
        """
        categories: dict[str, list[dict[str, Any]]] = {}

        for field_name, field in cls._fields.items():
            category_data = categories.setdefault(field.category, [])
            category_data.append(
                {
                    "name": field_name,
                    "display_name": field.display_name,
                    "description": field.description,
                    "type": field.field_type,
                }
            )

        return {"categories": categories, "total_fields": len(cls._fields)}


# Convenience function for quick access
def get_metric_field(field_name: str) -> MetricField | None:
    """Get a metric field by name."""
    return MetricFieldRegistry.get_field(field_name)


def get_available_metrics() -> list[str]:
    """Get list of all available metric field names."""
    return MetricFieldRegistry.get_available_field_names()
