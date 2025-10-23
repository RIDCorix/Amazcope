"""Service for aggregating and analyzing product metrics data.

This service provides helper methods for:
- Calculating metric changes and trends
- Comparing multiple products
- Generating summary statistics
- Time-range analysis
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from products.models import (
    Product,
    ProductSnapshot,
)
from schemas.metrics import (
    BSRTrendData,
    MetricComparisonResponse,
    MetricDataPoint,
    MetricsSummary,
    PriceTrendData,
    ProductMetricTrend,
    ReviewTrendData,
)


class MetricsAggregationService:
    """Service for aggregating and analyzing product metrics."""

    @staticmethod
    async def get_metrics_summary(db: AsyncSession, product_id: UUID) -> MetricsSummary | None:
        """Get summary statistics for a product with change percentages.

        Args:
            db: AsyncSession for database queries
            product_id: Product ID

        Returns:
            MetricsSummary with current values and 7d/30d changes, or None if no data
        """
        # Get latest metric
        stmt_latest = (
            select(ProductSnapshot)
            .where(
                ProductSnapshot.product_id == product_id,
            )
            .order_by(ProductSnapshot.scraped_at.desc())
            .limit(1)
        )
        result_latest = await db.execute(stmt_latest)
        latest = result_latest.scalar_one_or_none()

        # If no snapshots exist, return None (can't calculate metrics without data)
        if latest is None:
            raise ValueError(f"No snapshots found for product {product_id}")

        # Get metrics from 7 days ago
        date_7d_ago = datetime.utcnow() - timedelta(days=7)
        stmt_7d = (
            select(ProductSnapshot)
            .where(
                ProductSnapshot.product_id == product_id,
                ProductSnapshot.scraped_at <= date_7d_ago,
            )
            .order_by(ProductSnapshot.scraped_at.desc())
            .limit(1)
        )
        result_7d = await db.execute(stmt_7d)
        metric_7d = result_7d.scalar_one_or_none()

        # Get metrics from 30 days ago
        date_30d_ago = datetime.utcnow() - timedelta(days=30)
        stmt_30d = (
            select(ProductSnapshot)
            .where(
                ProductSnapshot.product_id == product_id,
                ProductSnapshot.scraped_at <= date_30d_ago,
            )
            .order_by(ProductSnapshot.scraped_at.desc())
            .limit(1)
        )
        result_30d = await db.execute(stmt_30d)
        metric_30d = result_30d.scalar_one_or_none()

        # Calculate changes (with None checks)
        # Extract values with None checks first
        # Using type: ignore because mypy doesn't properly narrow Optional types in if blocks
        price_7d: Decimal | float | None = None
        if metric_7d is not None:
            price_7d = metric_7d.price  # type: ignore[union-attr]

        price_30d: Decimal | float | None = None
        if metric_30d is not None:
            price_30d = metric_30d.price  # type: ignore[union-attr]

        bsr_7d: int | None = None
        if metric_7d is not None:
            bsr_7d = metric_7d.bsr_main_category  # type: ignore[union-attr]

        bsr_30d: int | None = None
        if metric_30d is not None:
            bsr_30d = metric_30d.bsr_main_category  # type: ignore[union-attr]

        rating_7d: Decimal | float | None = None
        if metric_7d is not None:
            rating_7d = metric_7d.rating  # type: ignore[union-attr]

        rating_30d: Decimal | float | None = None
        if metric_30d is not None:
            rating_30d = metric_30d.rating  # type: ignore[union-attr]

        review_count_7d: int | None = None
        if metric_7d is not None:
            review_count_7d = metric_7d.review_count  # type: ignore[union-attr]

        review_count_30d: int | None = None
        if metric_30d is not None:
            review_count_30d = metric_30d.review_count  # type: ignore[union-attr]

        price_change_7d = MetricsAggregationService._calculate_change(price_7d, latest.price)
        price_change_30d = MetricsAggregationService._calculate_change(price_30d, latest.price)
        bsr_change_7d = MetricsAggregationService._calculate_change(
            bsr_7d, latest.bsr_main_category
        )
        bsr_change_30d = MetricsAggregationService._calculate_change(
            bsr_30d, latest.bsr_main_category
        )
        rating_change_7d = MetricsAggregationService._calculate_change(rating_7d, latest.rating)
        rating_change_30d = MetricsAggregationService._calculate_change(rating_30d, latest.rating)

        review_growth_7d = (
            latest.review_count - review_count_7d if review_count_7d is not None else None
        )
        review_growth_30d = (
            latest.review_count - review_count_30d if review_count_30d is not None else None
        )

        return MetricsSummary(
            product_id=product_id,
            current_price=latest.price,
            price_change_7d=price_change_7d,
            price_change_30d=price_change_30d,
            current_bsr=latest.bsr_main_category,
            bsr_change_7d=bsr_change_7d,
            bsr_change_30d=bsr_change_30d,
            current_rating=latest.rating,
            rating_change_7d=rating_change_7d,
            rating_change_30d=rating_change_30d,
            review_count=latest.review_count,
            review_growth_7d=review_growth_7d,
            review_growth_30d=review_growth_30d,
            last_updated=latest.scraped_at,
        )

    @staticmethod
    async def get_product_comparison(
        db: AsyncSession, product_ids: list[UUID], metric_type: str, days: int = 30
    ) -> MetricComparisonResponse:
        """Get comparison data for multiple products.

        Args:
            db: AsyncSession for database queries
            product_ids: List of product IDs (max 10)
            metric_type: Type of metric ('price', 'bsr', 'rating', 'reviews')
            days: Number of days to include (default 30)

        Returns:
            MetricComparisonResponse with trend data for all products
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        products_data = []

        for product_id in product_ids[:10]:  # Limit to 10 products
            stmt_product = select(Product).where(Product.id == product_id)
            result_product = await db.execute(stmt_product)
            product = result_product.scalar_one_or_none()

            if not product:
                continue

            # Get metrics for date range
            stmt_metrics = (
                select(ProductSnapshot)
                .where(
                    ProductSnapshot.product_id == product_id,
                    ProductSnapshot.scraped_at >= start_date,
                    ProductSnapshot.scraped_at <= end_date,
                )
                .order_by(ProductSnapshot.scraped_at)
            )
            result_metrics = await db.execute(stmt_metrics)
            metrics = result_metrics.scalars().all()

            # Convert to appropriate trend data based on metric type
            data_points: list[PriceTrendData] | list[BSRTrendData] | list[ReviewTrendData]
            if metric_type == "price":
                data_points = [
                    PriceTrendData(
                        date=m.scraped_at,
                        price=float(m.price) if m.price is not None else None,
                        buybox_price=float(m.buybox_price) if m.buybox_price is not None else None,
                        original_price=float(m.original_price)
                        if m.original_price is not None
                        else None,
                        category_avg_price=(
                            float(m.category_avg_price)
                            if m.category_avg_price is not None
                            else None
                        ),
                    )
                    for m in metrics
                ]
            elif metric_type == "bsr":
                data_points = [
                    BSRTrendData(
                        date=m.scraped_at,
                        bsr_main=m.bsr_main_category,
                        bsr_small=m.bsr_small_category,
                    )
                    for m in metrics
                ]
            elif metric_type in ["rating", "reviews"]:
                data_points = [
                    ReviewTrendData(
                        date=m.scraped_at,
                        rating=m.rating,
                        review_count=m.review_count,
                        category_avg_rating=m.category_avg_rating,
                        category_avg_reviews=m.category_avg_reviews,
                    )
                    for m in metrics
                ]
            else:
                data_points = []

            products_data.append(
                ProductMetricTrend(
                    product_id=product.id,
                    product_title=product.title,
                    product_asin=product.asin,
                    data_points=data_points,
                )
            )

        # Get category average if available
        first_product_id = str(product_ids[0]) if product_ids else ""
        category_average = await MetricsAggregationService._get_category_average_trend(
            db,
            first_product_id,
            metric_type,
            start_date,
            end_date,
        )

        return MetricComparisonResponse(
            metric_type=metric_type,
            start_date=start_date,
            end_date=end_date,
            products=products_data,
            category_average=category_average,
        )

    @staticmethod
    async def _get_category_average_trend(
        db: AsyncSession,
        category: str,
        metric_field: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[MetricDataPoint] | None:
        """Get category average trend for a specific metric."""
        # TODO: Implement category average trend calculation
        return None

    @staticmethod
    def _calculate_change(
        old_value: float | Decimal | None, new_value: float | Decimal | None
    ) -> float | None:
        """Calculate percentage change between two values.

        Args:
            old_value: Previous value
            new_value: Current value

        Returns:
            Percentage change, or None if calculation not possible
        """
        if old_value is None or new_value is None:
            return None

        try:
            old = float(old_value)
            new = float(new_value)

            if old == 0:
                return None

            return ((new - old) / old) * 100
        except Exception as e:
            logger.error(f"Error calculating change: {e}")
            return None

    @staticmethod
    @staticmethod
    async def get_category_trend(
        db: AsyncSession, category_name: str, days: int = 30
    ) -> list[dict]:
        """Get category average trends for the last N days.

        Args:
            db: Database session
            category_name: Name of the category
            days: Number of days to fetch (default: 30)

        Returns:
            List of category metrics with timestamp and values
        """
        # TODO: Implement category trend calculation
        return []
