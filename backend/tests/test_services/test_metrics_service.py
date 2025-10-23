"""Tests for MetricsAggregationService."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from products.models import Product, ProductSnapshot
from services.metrics_service import MetricsAggregationService
from users.models import User


class TestCalculateChange:
    """Test percentage change calculation."""

    def test_calculate_positive_change(self):
        """Test calculating positive percentage change."""
        old_value = 100.0
        new_value = 120.0

        change = MetricsAggregationService._calculate_change(old_value, new_value)

        assert change == 20.0  # 20% increase

    def test_calculate_negative_change(self):
        """Test calculating negative percentage change."""
        old_value = 100.0
        new_value = 80.0

        change = MetricsAggregationService._calculate_change(old_value, new_value)

        assert change == -20.0  # 20% decrease

    def test_calculate_change_with_decimal(self):
        """Test calculating change with Decimal values."""
        old_value = Decimal("29.99")
        new_value = Decimal("34.99")

        change = MetricsAggregationService._calculate_change(old_value, new_value)

        assert change is not None
        assert abs(change - 16.67) < 0.1  # ~16.67% increase

    def test_calculate_change_none_old_value(self):
        """Test change calculation returns None when old value is None."""
        change = MetricsAggregationService._calculate_change(None, 100.0)

        assert change is None

    def test_calculate_change_none_new_value(self):
        """Test change calculation returns None when new value is None."""
        change = MetricsAggregationService._calculate_change(100.0, None)

        assert change is None

    def test_calculate_change_both_none(self):
        """Test change calculation returns None when both values are None."""
        change = MetricsAggregationService._calculate_change(None, None)

        assert change is None

    def test_calculate_change_zero_old_value(self):
        """Test change calculation returns None when old value is zero."""
        change = MetricsAggregationService._calculate_change(0, 100.0)

        assert change is None  # Can't divide by zero

    def test_calculate_change_no_change(self):
        """Test calculating change when values are the same."""
        old_value = 100.0
        new_value = 100.0

        change = MetricsAggregationService._calculate_change(old_value, new_value)

        assert change == 0.0


class TestGetMetricsSummary:
    """Test metrics summary generation."""

    @pytest.mark.asyncio
    async def test_get_metrics_summary_no_snapshots(
        self,
        db_session: AsyncSession,
    ):
        """Test metrics summary fails when no snapshots exist."""
        product_id = uuid4()

        with pytest.raises(ValueError, match="No snapshots found"):
            await MetricsAggregationService.get_metrics_summary(db_session, product_id)

    @pytest.mark.asyncio
    async def test_get_metrics_summary_with_current_only(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ):
        """Test metrics summary with only current snapshot."""
        # Create current snapshot
        snapshot = ProductSnapshot(
            product_id=test_product.id,
            price=Decimal("29.99"),
            bsr_main_category=1000,
            rating=Decimal("4.5"),
            review_count=100,
            scraped_at=datetime.utcnow(),
        )
        db_session.add(snapshot)
        await db_session.commit()

        summary = await MetricsAggregationService.get_metrics_summary(db_session, test_product.id)

        assert summary is not None
        assert summary.product_id == test_product.id
        assert summary.current_price == Decimal("29.99")
        assert summary.current_bsr == 1000
        assert summary.current_rating == Decimal("4.5")
        assert summary.review_count == 100
        # No historical data, so changes should be None
        assert summary.price_change_7d is None
        assert summary.price_change_30d is None

    @pytest.mark.asyncio
    async def test_get_metrics_summary_with_7d_history(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ):
        """Test metrics summary with 7-day historical data."""
        # Create snapshot from 7 days ago
        snapshot_7d = ProductSnapshot(
            product_id=test_product.id,
            price=Decimal("25.00"),
            bsr_main_category=1500,
            rating=Decimal("4.3"),
            review_count=80,
            scraped_at=datetime.utcnow() - timedelta(days=7),
        )
        db_session.add(snapshot_7d)

        # Create current snapshot
        snapshot_current = ProductSnapshot(
            product_id=test_product.id,
            price=Decimal("30.00"),
            bsr_main_category=1000,
            rating=Decimal("4.5"),
            review_count=100,
            scraped_at=datetime.utcnow(),
        )
        db_session.add(snapshot_current)
        await db_session.commit()

        summary = await MetricsAggregationService.get_metrics_summary(db_session, test_product.id)

        assert summary is not None
        assert summary.current_price == Decimal("30.00")
        # Price increased from 25 to 30 = 20% increase
        assert summary.price_change_7d == 20.0
        # BSR improved from 1500 to 1000 = -33.33% (negative is good for BSR)
        assert summary.bsr_change_7d is not None
        assert abs(summary.bsr_change_7d - (-33.33)) < 0.1
        # Rating improved from 4.3 to 4.5
        assert summary.rating_change_7d is not None
        # Review count grew by 20
        assert summary.review_growth_7d == 20

    @pytest.mark.asyncio
    async def test_get_metrics_summary_with_30d_history(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ):
        """Test metrics summary with 30-day historical data."""
        # Create snapshot from 30 days ago
        snapshot_30d = ProductSnapshot(
            product_id=test_product.id,
            price=Decimal("40.00"),
            bsr_main_category=2000,
            rating=Decimal("4.0"),
            review_count=50,
            scraped_at=datetime.utcnow() - timedelta(days=30),
        )
        db_session.add(snapshot_30d)

        # Create current snapshot
        snapshot_current = ProductSnapshot(
            product_id=test_product.id,
            price=Decimal("30.00"),
            bsr_main_category=1000,
            rating=Decimal("4.5"),
            review_count=100,
            scraped_at=datetime.utcnow(),
        )
        db_session.add(snapshot_current)
        await db_session.commit()

        summary = await MetricsAggregationService.get_metrics_summary(db_session, test_product.id)

        assert summary is not None
        # Price decreased from 40 to 30 = -25% decrease
        assert summary.price_change_30d == -25.0
        # BSR improved from 2000 to 1000 = -50%
        assert summary.bsr_change_30d == -50.0
        # Review count grew by 50
        assert summary.review_growth_30d == 50


class TestGetProductComparison:
    """Test product comparison functionality."""

    @pytest.mark.asyncio
    async def test_get_product_comparison_single_product_price(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ):
        """Test comparing price data for a single product."""
        # Create snapshots over 10 days
        for days_ago in range(10, 0, -1):
            snapshot = ProductSnapshot(
                product_id=test_product.id,
                price=Decimal(f"{25 + days_ago}.99"),
                scraped_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db_session.add(snapshot)
        await db_session.commit()

        comparison = await MetricsAggregationService.get_product_comparison(
            db=db_session,
            product_ids=[test_product.id],
            metric_type="price",
            days=10,
        )

        assert comparison is not None
        assert comparison.metric_type == "price"
        assert len(comparison.products) == 1
        assert comparison.products[0].product_id == test_product.id
        # Service may return N-1 data points (filters current/today snapshots)
        assert len(comparison.products[0].data_points) >= 9

    @pytest.mark.asyncio
    async def test_get_product_comparison_bsr_metric(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ):
        """Test comparing BSR data."""
        # Create snapshots with BSR data
        for days_ago in range(5, 0, -1):
            snapshot = ProductSnapshot(
                product_id=test_product.id,
                bsr_main_category=1000 + (days_ago * 100),
                bsr_small_category=500 + (days_ago * 50),
                scraped_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db_session.add(snapshot)
        await db_session.commit()

        comparison = await MetricsAggregationService.get_product_comparison(
            db=db_session,
            product_ids=[test_product.id],
            metric_type="bsr",
            days=5,
        )

        assert comparison is not None
        assert comparison.metric_type == "bsr"
        # Service may return N-1 data points (filters current/today snapshots)
        assert len(comparison.products[0].data_points) >= 4
        # Verify BSR data structure
        first_point = comparison.products[0].data_points[0]
        assert hasattr(first_point, "bsr_main")
        assert hasattr(first_point, "bsr_small")

    @pytest.mark.asyncio
    async def test_get_product_comparison_reviews_metric(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ):
        """Test comparing review/rating data."""
        # Create snapshots with review data
        for days_ago in range(5, 0, -1):
            snapshot = ProductSnapshot(
                product_id=test_product.id,
                rating=Decimal("4.0") + Decimal(str(days_ago * 0.1)),
                review_count=100 + (days_ago * 10),
                scraped_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db_session.add(snapshot)
        await db_session.commit()

        comparison = await MetricsAggregationService.get_product_comparison(
            db=db_session,
            product_ids=[test_product.id],
            metric_type="reviews",
            days=5,
        )

        assert comparison is not None
        assert comparison.metric_type == "reviews"
        # Service may return N-1 data points (filters current/today snapshots)
        assert len(comparison.products[0].data_points) >= 4

    @pytest.mark.asyncio
    async def test_get_product_comparison_multiple_products(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test comparing multiple products."""
        # Create two products
        product1 = Product(
            asin="B001TEST1",
            marketplace="com",
            title="Product 1",
            url="https://www.amazon.com/dp/B001TEST1",
        )
        product2 = Product(
            asin="B002TEST2",
            marketplace="com",
            title="Product 2",
            url="https://www.amazon.com/dp/B002TEST2",
        )
        db_session.add_all([product1, product2])
        await db_session.commit()
        await db_session.refresh(product1)
        await db_session.refresh(product2)

        # Create snapshots for both products
        for product in [product1, product2]:
            for days_ago in range(3, 0, -1):
                snapshot = ProductSnapshot(
                    product_id=product.id,
                    price=Decimal(f"{30 + days_ago}.00"),
                    scraped_at=datetime.utcnow() - timedelta(days=days_ago),
                )
                db_session.add(snapshot)
        await db_session.commit()

        comparison = await MetricsAggregationService.get_product_comparison(
            db=db_session,
            product_ids=[product1.id, product2.id],
            metric_type="price",
            days=3,
        )

        assert comparison is not None
        assert len(comparison.products) == 2
        assert comparison.products[0].product_asin in ["B001TEST1", "B002TEST2"]

    @pytest.mark.asyncio
    async def test_get_product_comparison_limit_10_products(
        self,
        db_session: AsyncSession,
    ):
        """Test that comparison limits to 10 products."""
        # Create 15 products
        product_ids = []
        for i in range(15):
            product = Product(
                asin=f"B00{i:02d}TEST",
                marketplace="com",
                title=f"Product {i}",
                url=f"https://www.amazon.com/dp/B00{i:02d}TEST",
            )
            db_session.add(product)
            await db_session.commit()
            await db_session.refresh(product)
            product_ids.append(product.id)

            # Add snapshot
            snapshot = ProductSnapshot(
                product_id=product.id,
                price=Decimal("29.99"),
                scraped_at=datetime.utcnow(),
            )
            db_session.add(snapshot)

        await db_session.commit()

        comparison = await MetricsAggregationService.get_product_comparison(
            db=db_session,
            product_ids=product_ids,
            metric_type="price",
            days=1,
        )

        # Should limit to 10 products
        assert len(comparison.products) <= 10


class TestGetCategoryTrend:
    """Test category trend functionality."""

    @pytest.mark.asyncio
    async def test_get_category_trend_returns_empty_list(
        self,
        db_session: AsyncSession,
    ):
        """Test get_category_trend returns empty list (not yet implemented)."""
        result = await MetricsAggregationService.get_category_trend(
            db=db_session,
            category_name="Electronics",
            days=30,
        )

        assert result == []


class TestMetricsEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_metrics_summary_with_null_price_values(
        self,
        db_session: AsyncSession,
        test_product: Product,
    ):
        """Test metrics summary handles null price values."""
        # Create snapshot with null price
        snapshot = ProductSnapshot(
            product_id=test_product.id,
            price=None,  # Null price
            bsr_main_category=1000,
            scraped_at=datetime.utcnow(),
        )
        db_session.add(snapshot)
        await db_session.commit()

        summary = await MetricsAggregationService.get_metrics_summary(db_session, test_product.id)

        assert summary is not None
        assert summary.current_price is None

    @pytest.mark.asyncio
    async def test_product_comparison_nonexistent_product(
        self,
        db_session: AsyncSession,
    ):
        """Test product comparison skips nonexistent products."""
        fake_id = uuid4()

        comparison = await MetricsAggregationService.get_product_comparison(
            db=db_session,
            product_ids=[fake_id],
            metric_type="price",
            days=7,
        )

        assert comparison is not None
        assert len(comparison.products) == 0  # Nonexistent product skipped

    @pytest.mark.asyncio
    async def test_product_comparison_empty_product_list(
        self,
        db_session: AsyncSession,
    ):
        """Test product comparison with empty product list."""
        comparison = await MetricsAggregationService.get_product_comparison(
            db=db_session,
            product_ids=[],
            metric_type="price",
            days=7,
        )

        assert comparison is not None
        assert len(comparison.products) == 0
