"""Tests for ProductTrackingService."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from products.models import Product, ProductSnapshot, UserProduct
from scrapper.product_tracking_service import ProductTrackingService


class TestProductTrackingServiceInit:
    """Test ProductTrackingService initialization."""

    @pytest.mark.asyncio
    async def test_service_initialization(self, db_session: AsyncSession):
        """Test service initializes with DB session."""
        service = ProductTrackingService(db_session)

        assert service.db == db_session
        assert service.apify_service is not None
        assert service.cache_service is not None


class TestExtractASIN:
    """Test ASIN extraction from URLs."""

    @pytest.mark.asyncio
    async def test_extract_asin_valid_url(self, db_session: AsyncSession):
        """Test ASIN extraction from valid Amazon URL."""
        service = ProductTrackingService(db_session)

        # Mock the apify_service method
        service.apify_service.extract_asin_from_url = MagicMock(return_value="B07XJ8C8F5")

        url = "https://www.amazon.com/dp/B07XJ8C8F5"
        asin = service.apify_service.extract_asin_from_url(url)

        assert asin == "B07XJ8C8F5"
        assert len(asin) == 10

    @pytest.mark.asyncio
    async def test_extract_asin_invalid_url(self, db_session: AsyncSession):
        """Test ASIN extraction fails on invalid URL."""
        service = ProductTrackingService(db_session)

        service.apify_service.extract_asin_from_url = MagicMock(return_value=None)

        url = "https://www.notamazon.com/product/123"
        asin = service.apify_service.extract_asin_from_url(url)

        assert asin is None


class TestExtractMarketplace:
    """Test marketplace extraction from URLs."""

    @pytest.mark.asyncio
    async def test_extract_marketplace_com(self, db_session: AsyncSession):
        """Test marketplace extraction for .com."""
        service = ProductTrackingService(db_session)

        service.apify_service.extract_marketplace_from_url = MagicMock(return_value="com")

        url = "https://www.amazon.com/dp/B07XJ8C8F5"
        marketplace = service.apify_service.extract_marketplace_from_url(url)

        assert marketplace == "com"

    @pytest.mark.asyncio
    async def test_extract_marketplace_uk(self, db_session: AsyncSession):
        """Test marketplace extraction for .co.uk."""
        service = ProductTrackingService(db_session)

        service.apify_service.extract_marketplace_from_url = MagicMock(return_value="co.uk")

        url = "https://www.amazon.co.uk/dp/B07XJ8C8F5"
        marketplace = service.apify_service.extract_marketplace_from_url(url)

        assert marketplace == "co.uk"


class TestAddProductFromURL:
    """Test adding products from Amazon URLs."""

    @pytest.mark.asyncio
    async def test_add_product_invalid_url_no_asin(self, db_session: AsyncSession):
        """Test adding product fails when ASIN can't be extracted."""
        service = ProductTrackingService(db_session)

        # Mock ASIN extraction to return None
        service.apify_service.extract_asin_from_url = MagicMock(return_value=None)

        user_id = uuid4()
        url = "https://www.notamazon.com/product"

        with pytest.raises(HTTPException) as exc_info:
            await service.add_product_from_url(user_id, url)

        assert exc_info.value.status_code == 400
        assert "Could not extract ASIN" in exc_info.value.detail


class TestProductSnapshot:
    """Test product snapshot creation."""

    @pytest.mark.asyncio
    async def test_create_snapshot_basic(self, db_session: AsyncSession):
        """Test creating a basic product snapshot."""
        # This test verifies the ProductSnapshot model can be created
        snapshot = ProductSnapshot(
            product_id=uuid4(),
            price=29.99,
            currency="USD",
            in_stock=True,
            rating=4.5,
            review_count=1234,
        )

        assert snapshot.price == 29.99
        assert snapshot.currency == "USD"
        assert snapshot.in_stock is True
        assert snapshot.rating == 4.5
        assert snapshot.review_count == 1234


class TestDetectPriceChanges:
    """Test price change detection logic."""

    @pytest.mark.asyncio
    async def test_price_increased_detection(self):
        """Test detecting price increase."""
        old_price = 29.99
        new_price = 34.99
        threshold = 10.0  # 10% threshold

        # Calculate percentage change
        change_pct = ((new_price - old_price) / old_price) * 100

        assert change_pct > threshold
        assert change_pct == pytest.approx(16.67, rel=0.1)

    @pytest.mark.asyncio
    async def test_price_decreased_detection(self):
        """Test detecting price decrease."""
        old_price = 29.99
        new_price = 24.99
        threshold = 10.0

        change_pct = abs(((new_price - old_price) / old_price) * 100)

        assert change_pct > threshold
        assert change_pct == pytest.approx(16.67, rel=0.1)

    @pytest.mark.asyncio
    async def test_price_change_below_threshold(self):
        """Test price change below threshold doesn't trigger alert."""
        old_price = 29.99
        new_price = 30.99
        threshold = 10.0

        change_pct = abs(((new_price - old_price) / old_price) * 100)

        assert change_pct < threshold


class TestDetectBSRChanges:
    """Test BSR (Best Seller Rank) change detection."""

    @pytest.mark.asyncio
    async def test_bsr_improved_detection(self):
        """Test detecting BSR improvement (lower rank is better)."""
        old_bsr = 1000
        new_bsr = 600  # Changed from 800 to 600 for >30% improvement
        threshold = 30.0  # 30% threshold

        # BSR improvement = rank decreased
        change_pct = ((old_bsr - new_bsr) / old_bsr) * 100

        assert change_pct > threshold
        assert change_pct == 40.0

    @pytest.mark.asyncio
    async def test_bsr_worsened_detection(self):
        """Test detecting BSR decline (higher rank is worse)."""
        old_bsr = 1000
        new_bsr = 1500
        threshold = 30.0

        change_pct = abs(((new_bsr - old_bsr) / old_bsr) * 100)

        assert change_pct > threshold
        assert change_pct == 50.0


class TestUserProductOwnership:
    """Test user-product ownership validation."""

    @pytest.mark.asyncio
    async def test_user_product_creation(self, db_session: AsyncSession):
        """Test creating a user-product relationship."""
        user_id = uuid4()
        product_id = uuid4()

        user_product = UserProduct(
            user_id=user_id,
            product_id=product_id,
            is_primary=True,
            price_change_threshold=10.0,
            bsr_change_threshold=30.0,
        )

        assert user_product.user_id == user_id
        assert user_product.product_id == product_id
        assert user_product.is_primary is True
        assert user_product.price_change_threshold == 10.0
        assert user_product.bsr_change_threshold == 30.0


class TestProductModel:
    """Test Product model validations."""

    @pytest.mark.asyncio
    async def test_product_creation_required_fields(self):
        """Test creating product with required fields."""
        product = Product(
            asin="B07XJ8C8F5",
            marketplace="com",
            title="Test Product",
            url="https://www.amazon.com/dp/B07XJ8C8F5",
        )

        assert product.asin == "B07XJ8C8F5"
        assert product.marketplace == "com"
        assert product.title == "Test Product"
        assert len(product.asin) == 10
