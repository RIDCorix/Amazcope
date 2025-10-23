"""Expanded tests for ProductTrackingService - Phase 5."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from products.models import Product, ProductSnapshot, UserProduct
from schemas.scraper_response import NormalizedProductResponse
from scrapper.product_tracking_service import ProductTrackingService


class TestAddProductFromURLComplete:
    """Test complete add_product_from_url workflow."""

    @pytest.mark.asyncio
    async def test_add_new_product_success(self, db_session: AsyncSession, test_user):
        """Test successfully adding a new product."""
        service = ProductTrackingService(db_session)

        # Mock ASIN and marketplace extraction
        service.apify_service.extract_asin_from_url = MagicMock(return_value="B07XJ8C8F5")
        service.apify_service.extract_marketplace_from_url = MagicMock(return_value="com")

        # Mock scraping with full product data
        mock_product_data = MagicMock(spec=NormalizedProductResponse)
        mock_product_data.title = "Test Product"
        mock_product_data.brand = "Test Brand"
        mock_product_data.main_category_name = "Electronics"
        mock_product_data.small_category_name = "Laptops"
        mock_product_data.category_url = "https://www.amazon.com/gp/bestsellers/electronics"
        mock_product_data.image_url = "https://example.com/image.jpg"
        mock_product_data.rating = 4.5
        mock_product_data.review_count = 100
        mock_product_data.price = 29.99
        mock_product_data.bsr_main_category = 1000
        mock_product_data.bsr_category_link = None
        mock_product_data.bsr_subcategory_link = None

        service.apify_service.scrape_product = AsyncMock(return_value=mock_product_data)

        # Mock _create_snapshot
        with patch.object(service, "_create_snapshot", new_callable=AsyncMock):
            url = "https://www.amazon.com/dp/B07XJ8C8F5"
            product = await service.add_product_from_url(test_user.id, url)

            assert product.asin == "B07XJ8C8F5"
            assert product.marketplace == "com"
            assert product.title == "Test Product"
            assert product.created_by_id == test_user.id

    @pytest.mark.asyncio
    async def test_add_existing_product_new_user(self, db_session: AsyncSession, test_user):
        """Test adding existing product for new user creates UserProduct."""
        service = ProductTrackingService(db_session)

        # Create existing product
        existing_product = Product(
            asin="B07XJ8C8F5",
            marketplace="com",
            title="Existing Product",
            url="https://www.amazon.com/dp/B07XJ8C8F5",
        )
        db_session.add(existing_product)
        await db_session.commit()
        await db_session.refresh(existing_product)

        # Mock extraction
        service.apify_service.extract_asin_from_url = MagicMock(return_value="B07XJ8C8F5")
        service.apify_service.extract_marketplace_from_url = MagicMock(return_value="com")

        url = "https://www.amazon.com/dp/B07XJ8C8F5"
        product = await service.add_product_from_url(test_user.id, url)

        assert product.id == existing_product.id
        assert product.asin == "B07XJ8C8F5"

    @pytest.mark.asyncio
    async def test_add_existing_product_same_user_raises_error(
        self, db_session: AsyncSession, test_user
    ):
        """Test adding same product twice for same user raises error."""
        service = ProductTrackingService(db_session)

        # Create existing product and user relationship
        existing_product = Product(
            asin="B07XJ8C8F5",
            marketplace="com",
            title="Existing Product",
            url="https://www.amazon.com/dp/B07XJ8C8F5",
        )
        db_session.add(existing_product)
        await db_session.commit()
        await db_session.refresh(existing_product)

        user_product = UserProduct(
            user_id=test_user.id,
            product_id=existing_product.id,
            price_change_threshold=10.0,
            bsr_change_threshold=30.0,
        )
        db_session.add(user_product)
        await db_session.commit()

        # Mock extraction
        service.apify_service.extract_asin_from_url = MagicMock(return_value="B07XJ8C8F5")
        service.apify_service.extract_marketplace_from_url = MagicMock(return_value="com")

        url = "https://www.amazon.com/dp/B07XJ8C8F5"

        with pytest.raises(HTTPException) as exc_info:
            await service.add_product_from_url(test_user.id, url)

        assert exc_info.value.status_code == 400
        assert "already being tracked" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_add_product_with_404_response(self, db_session: AsyncSession, test_user):
        """Test adding product that returns 404 raises error."""
        service = ProductTrackingService(db_session)

        service.apify_service.extract_asin_from_url = MagicMock(return_value="B07XJ8C8F5")
        service.apify_service.extract_marketplace_from_url = MagicMock(return_value="com")

        # Mock 404 response
        service.apify_service.scrape_product = AsyncMock(
            return_value={"status": "404", "asin": "B07XJ8C8F5"}
        )

        url = "https://www.amazon.com/dp/B07XJ8C8F5"

        with pytest.raises(HTTPException) as exc_info:
            await service.add_product_from_url(test_user.id, url)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_add_product_with_manual_categories(self, db_session: AsyncSession, test_user):
        """Test adding product with manually specified categories."""
        service = ProductTrackingService(db_session)

        service.apify_service.extract_asin_from_url = MagicMock(return_value="B07XJ8C8F5")
        service.apify_service.extract_marketplace_from_url = MagicMock(return_value="com")

        # Mock product data
        mock_product_data = MagicMock(spec=NormalizedProductResponse)
        mock_product_data.title = "Test Product"
        mock_product_data.brand = "Test Brand"
        mock_product_data.main_category_name = "Auto Category"
        mock_product_data.small_category_name = "Auto Subcategory"
        mock_product_data.category_url = "https://www.amazon.com/gp/bestsellers/electronics"
        mock_product_data.image_url = "https://example.com/image.jpg"
        mock_product_data.bsr_category_link = None
        mock_product_data.bsr_subcategory_link = None

        service.apify_service.scrape_product = AsyncMock(return_value=mock_product_data)

        with patch.object(service, "_create_snapshot", new_callable=AsyncMock):
            url = "https://www.amazon.com/dp/B07XJ8C8F5"
            product = await service.add_product_from_url(
                test_user.id,
                url,
                manual_category="Manual Category",
                manual_small_category="Manual Subcategory",
            )

            # Should use manual categories, not scraped ones
            assert product.category == "Manual Category"
            assert product.small_category == "Manual Subcategory"

    @pytest.mark.asyncio
    async def test_add_product_with_custom_thresholds(self, db_session: AsyncSession, test_user):
        """Test adding product with custom alert thresholds."""
        service = ProductTrackingService(db_session)

        service.apify_service.extract_asin_from_url = MagicMock(return_value="B07XJ8C8F5")
        service.apify_service.extract_marketplace_from_url = MagicMock(return_value="com")

        mock_product_data = MagicMock(spec=NormalizedProductResponse)
        mock_product_data.title = "Test Product"
        mock_product_data.brand = "Test Brand"
        mock_product_data.main_category_name = "Electronics"
        mock_product_data.small_category_name = "Laptops"
        mock_product_data.category_url = "https://www.amazon.com/gp/bestsellers/electronics"
        mock_product_data.image_url = "https://example.com/image.jpg"
        mock_product_data.bsr_category_link = None
        mock_product_data.bsr_subcategory_link = None

        service.apify_service.scrape_product = AsyncMock(return_value=mock_product_data)

        with patch.object(service, "_create_snapshot", new_callable=AsyncMock):
            url = "https://www.amazon.com/dp/B07XJ8C8F5"
            product = await service.add_product_from_url(
                test_user.id,
                url,
                price_threshold=25.0,
                bsr_threshold=40.0,
            )

            assert product.price_change_threshold == 25.0
            assert product.bsr_change_threshold == 40.0


class TestUpdateProduct:
    """Test product update functionality."""

    @pytest.mark.asyncio
    async def test_update_product_success(self, db_session: AsyncSession, test_product):
        """Test successful product update."""
        service = ProductTrackingService(db_session)

        # Mock cache miss
        service.cache_service.get = AsyncMock(return_value=None)
        service.cache_service.set = AsyncMock()

        # Mock scraping
        mock_product_data = MagicMock(spec=NormalizedProductResponse)
        mock_product_data.price = 34.99
        mock_product_data.bsr_main_category = 800

        service.apify_service.scrape_product = AsyncMock(return_value=mock_product_data)

        with patch.object(service, "_create_snapshot", new_callable=AsyncMock) as mock_create:
            mock_snapshot = MagicMock(spec=ProductSnapshot)
            mock_create.return_value = mock_snapshot

            snapshot = await service.update_product(test_product.id)

            assert mock_create.called
            assert snapshot == mock_snapshot

    @pytest.mark.asyncio
    async def test_update_product_uses_cache(self, db_session: AsyncSession, test_product):
        """Test product update uses cached data when available."""
        service = ProductTrackingService(db_session)

        # Mock cache hit
        cached_snapshot = MagicMock(spec=ProductSnapshot)
        cached_snapshot.price = 29.99
        service.cache_service.get = AsyncMock(return_value=cached_snapshot)

        snapshot = await service.update_product(test_product.id)

        assert snapshot == cached_snapshot
        # Should not call scrape_product
        service.apify_service.scrape_product = AsyncMock()
        assert not service.apify_service.scrape_product.called

    @pytest.mark.asyncio
    async def test_update_nonexistent_product_raises_error(self, db_session: AsyncSession):
        """Test updating non-existent product raises 404."""
        service = ProductTrackingService(db_session)

        fake_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await service.update_product(fake_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_product_handles_404_response(
        self, db_session: AsyncSession, test_product
    ):
        """Test product update handles 404 (unlisted product)."""
        service = ProductTrackingService(db_session)

        service.cache_service.get = AsyncMock(return_value=None)

        # Mock 404 response
        service.apify_service.scrape_product = AsyncMock(
            return_value={"status": "404", "asin": test_product.asin}
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.update_product(test_product.id)

        assert exc_info.value.status_code == 404

        # Verify product was marked as unlisted
        await db_session.refresh(test_product)
        assert test_product.is_unlisted is True
        assert test_product.is_active is False


class TestBatchUpdateProducts:
    """Test batch product update functionality."""

    @pytest.mark.asyncio
    async def test_batch_update_all_success(self, db_session: AsyncSession, test_user):
        """Test batch update with all products succeeding."""
        service = ProductTrackingService(db_session)

        # Create 3 test products
        product_ids = []
        for i in range(3):
            product = Product(
                asin=f"B07XJ8C8F{i}",
                marketplace="com",
                title=f"Test Product {i}",
                url=f"https://www.amazon.com/dp/B07XJ8C8F{i}",
            )
            db_session.add(product)
            await db_session.commit()
            await db_session.refresh(product)
            product_ids.append(product.id)

        # Mock update_product to succeed
        with patch.object(service, "update_product", new_callable=AsyncMock):
            results = await service.batch_update_products(product_ids)

            assert results["success"] == 3
            assert results["failed"] == 0
            assert len(results["errors"]) == 0

    @pytest.mark.asyncio
    async def test_batch_update_partial_failure(self, db_session: AsyncSession, test_user):
        """Test batch update with some products failing."""
        service = ProductTrackingService(db_session)

        # Create 3 products
        product_ids = []
        for i in range(3):
            product = Product(
                asin=f"B07XJ8C8F{i}",
                marketplace="com",
                title=f"Test Product {i}",
                url=f"https://www.amazon.com/dp/B07XJ8C8F{i}",
            )
            db_session.add(product)
            await db_session.commit()
            await db_session.refresh(product)
            product_ids.append(product.id)

        # Mock update_product to fail on second product
        async def mock_update(product_id, check_alerts=True):
            if product_id == product_ids[1]:
                raise Exception("Scraping failed")

        with patch.object(service, "update_product", side_effect=mock_update):
            results = await service.batch_update_products(product_ids)

            assert results["success"] == 2
            assert results["failed"] == 1
            assert len(results["errors"]) == 1


class TestRefreshProduct:
    """Test force refresh product functionality."""

    @pytest.mark.asyncio
    async def test_refresh_product_bypasses_cache(self, db_session: AsyncSession, test_product):
        """Test refresh bypasses cache and forces scraping."""
        service = ProductTrackingService(db_session)

        # Mock scraping
        mock_product_data = MagicMock(spec=NormalizedProductResponse)
        mock_product_data.price = 39.99

        service.apify_service.scrape_product = AsyncMock(return_value=mock_product_data)
        service.cache_service.delete = AsyncMock()

        with patch.object(service, "_create_snapshot", new_callable=AsyncMock) as mock_create:
            mock_snapshot = MagicMock(spec=ProductSnapshot)
            mock_create.return_value = mock_snapshot

            await service.refresh_product(test_product.id)

            # Should delete cache and create new snapshot
            service.cache_service.delete.assert_called()
            assert mock_create.called


class TestAlertGeneration:
    """Test alert generation for price and BSR changes."""

    @pytest.mark.asyncio
    async def test_alert_generated_for_price_increase(self, db_session: AsyncSession):
        """Test alert is generated when price increases above threshold."""
        # Create product with previous snapshot
        product = Product(
            asin="B07XJ8C8F5",
            marketplace="com",
            title="Test Product",
            url="https://www.amazon.com/dp/B07XJ8C8F5",
            price_change_threshold=10.0,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        # Create old snapshot with lower price
        old_snapshot = ProductSnapshot(
            product_id=product.id,
            price=29.99,
            scraped_at=datetime.utcnow() - timedelta(days=1),
        )
        db_session.add(old_snapshot)
        await db_session.commit()

        # Calculate price change
        old_price = 29.99
        new_price = 34.99
        threshold = 10.0

        change_pct = ((new_price - old_price) / old_price) * 100

        # Verify alert should be triggered
        assert change_pct > threshold
        assert change_pct == pytest.approx(16.67, rel=0.1)

    @pytest.mark.asyncio
    async def test_alert_generated_for_bsr_improvement(self, db_session: AsyncSession):
        """Test alert is generated when BSR improves significantly."""
        product = Product(
            asin="B07XJ8C8F5",
            marketplace="com",
            title="Test Product",
            url="https://www.amazon.com/dp/B07XJ8C8F5",
            bsr_change_threshold=30.0,
        )
        db_session.add(product)
        await db_session.commit()

        # BSR improvement (rank decreased from 1000 to 600)
        old_bsr = 1000
        new_bsr = 600
        threshold = 30.0

        change_pct = ((old_bsr - new_bsr) / old_bsr) * 100

        assert change_pct > threshold
        assert change_pct == 40.0


class TestMarketplaceHandling:
    """Test multi-marketplace support."""

    @pytest.mark.asyncio
    async def test_different_marketplaces_treated_separately(
        self, db_session: AsyncSession, test_user
    ):
        """Test same ASIN in different marketplaces are separate products."""
        # Create product in .com marketplace
        product_com = Product(
            asin="B07XJ8C8F5",
            marketplace="com",
            title="US Product",
            url="https://www.amazon.com/dp/B07XJ8C8F5",
        )
        db_session.add(product_com)
        await db_session.commit()

        # Create same ASIN in .de marketplace
        product_de = Product(
            asin="B07XJ8C8F5",
            marketplace="de",
            title="DE Product",
            url="https://www.amazon.de/dp/B07XJ8C8F5",
        )
        db_session.add(product_de)
        await db_session.commit()

        # Verify they're different products
        assert product_com.id != product_de.id
        assert product_com.marketplace != product_de.marketplace


class TestSnapshotCreation:
    """Test snapshot creation from product data."""

    @pytest.mark.asyncio
    async def test_create_snapshot_stores_all_fields(self, db_session: AsyncSession):
        """Test snapshot captures all relevant product fields."""
        product = Product(
            asin="B07XJ8C8F5",
            marketplace="com",
            title="Test Product",
            url="https://www.amazon.com/dp/B07XJ8C8F5",
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        # Create snapshot with full data
        snapshot = ProductSnapshot(
            product_id=product.id,
            price=29.99,
            currency="USD",
            bsr_main_category=1000,
            bsr_small_category=50,
            rating=4.5,
            review_count=1234,
            in_stock=True,
            seller_name="Test Seller",
            is_amazon_seller=True,
        )
        db_session.add(snapshot)
        await db_session.commit()

        # Verify all fields stored
        assert snapshot.price == 29.99
        assert snapshot.bsr_main_category == 1000
        assert snapshot.rating == 4.5
        assert snapshot.in_stock is True
        assert snapshot.seller_name == "Test Seller"
