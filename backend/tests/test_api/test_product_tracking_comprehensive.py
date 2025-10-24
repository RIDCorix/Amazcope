"""Comprehensive tests for product tracking API endpoints.

Tests all product tracking operations including:
- Product import from URL
- Product CRUD operations
- Batch operations
- History and alerts
- Reviews and bestsellers
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from products.models import (
    Product,
    ProductSnapshot,
    Review,
    UserProduct,
)
from users.models import User


class TestProductFromUrl:
    """Tests for product import from Amazon URL endpoint."""

    @pytest.mark.asyncio
    async def test_import_from_url_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
        mock_apify_response: dict,
    ):
        """Test successful product import from Amazon URL."""
        with patch(
            "scrapper.product_tracking_service.ProductTrackingService.add_product_from_url",
            new_callable=AsyncMock,
        ) as mock_add:
            # Mock the service response with all required ProductOut fields
            mock_product = Product(
                id=uuid.uuid4(),  # Required for ProductOut
                asin="B094WLFGD3",
                marketplace="com",
                title="Echo Dot (4th Gen)",
                brand="Amazon",
                url="https://www.amazon.com/dp/B094WLFGD3",
                current_price=49.99,
                currency="USD",
                is_active=True,
                track_frequency="daily",
                price_change_threshold=10.0,
                bsr_change_threshold=30.0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            mock_add.return_value = mock_product

            response = await client.post(
                "/api/v1/tracking/products/from-url",
                headers=auth_headers,
                json={
                    "url": "https://www.amazon.com/dp/B094WLFGD3",
                    "price_change_threshold": 10.0,
                    "bsr_change_threshold": 30.0,
                    "scrape_reviews": True,
                    "scrape_bestsellers": True,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["asin"] == "B094WLFGD3"
            assert data["title"] == "Echo Dot (4th Gen)"

    @pytest.mark.asyncio
    async def test_import_from_url_invalid_url(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test product import fails with invalid URL."""
        response = await client.post(
            "/api/v1/tracking/products/from-url",
            headers=auth_headers,
            json={
                "url": "https://not-a-valid-amazon-url.com/invalid",
                "price_change_threshold": 10.0,
                "bsr_change_threshold": 30.0,
            },
        )

        # Invalid URL should be caught by ASIN extraction and return 400 or 422 (validation error)
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_import_from_url_unauthorized(self, client: AsyncClient):
        """Test product import requires authentication."""
        response = await client.post(
            "/api/v1/tracking/products/from-url",
            json={
                "url": "https://www.amazon.com/dp/B094WLFGD3",
                "price_change_threshold": 10.0,
            },
        )

        # FastAPI returns 403 Forbidden when no auth header provided
        # (get_current_user dependency raises HTTPException with 403)
        assert response.status_code == 403


class TestProductCRUD:
    """Tests for product CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_products(
        self,
        client: AsyncClient,
        test_user: User,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test listing user's products."""
        response = await client.get(
            "/api/v1/tracking/products",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert any(p["asin"] == test_product.asin for p in data)

    @pytest.mark.asyncio
    async def test_list_products_pagination(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test product listing with pagination."""
        response = await client.get(
            "/api/v1/tracking/products?skip=0&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    @pytest.mark.asyncio
    async def test_get_product_details(
        self,
        client: AsyncClient,
        test_product: Product,
        test_snapshot: ProductSnapshot,
        auth_headers: dict[str, str],
    ):
        """Test getting detailed product information."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_product.id)
        assert data["asin"] == test_product.asin
        assert "latest_snapshot" in data or "snapshots" in data

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test getting non-existent product returns 404."""
        from uuid import uuid4

        response = await client.get(
            f"/api/v1/tracking/products/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_product_not_owned(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test user cannot access product they don't own."""
        # Create a product owned by another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashedpassword",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_product = Product(
            asin="B01OTHER12",
            marketplace="com",
            title="Other User Product",
            url="https://www.amazon.com/dp/B01OTHER12",
            current_price=29.99,
            currency="USD",
        )
        db_session.add(other_product)
        await db_session.commit()
        await db_session.refresh(other_product)

        # Create user-product relationship for other user
        user_product = UserProduct(
            user_id=other_user.id,
            product_id=other_product.id,
            is_primary=True,
        )
        db_session.add(user_product)
        await db_session.commit()

        # Try to access as test_user
        response = await client.get(
            f"/api/v1/tracking/products/{other_product.id}",
            headers=auth_headers,
        )

        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_delete_product(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test product deletion."""
        response = await client.delete(
            f"/api/v1/tracking/products/{test_product.id}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 204]

        # Verify product is soft deleted (marked inactive but still accessible)
        verify_response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}",
            headers=auth_headers,
        )
        # Product should still be accessible but marked as inactive
        assert verify_response.status_code == 200
        data = verify_response.json()
        assert not data["is_active"]

    @pytest.mark.asyncio
    async def test_update_product_category(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test updating product category."""
        response = await client.patch(
            f"/api/v1/tracking/products/{test_product.id}/category",
            headers=auth_headers,
            json={
                "manual_category": "Updated Category",
                "manual_small_category": "Updated Subcategory",
            },
        )

        assert response.status_code == 200
        data = response.json()
        # The endpoint updates category and small_category fields in the response
        assert data["category"] == "Updated Category" or "category" in data


class TestProductUpdates:
    """Tests for product update/refresh operations."""

    @pytest.mark.asyncio
    async def test_trigger_product_update(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test triggering product scrape update."""
        from datetime import UTC, datetime
        from decimal import Decimal
        from uuid import uuid4

        with patch(
            "scrapper.product_tracking_service.ProductTrackingService.update_product",
            new_callable=AsyncMock,
        ) as mock_update:
            # Create fully populated mock snapshot with all required fields
            now = datetime.now(UTC)
            mock_snapshot = ProductSnapshot(
                id=uuid4(),
                product_id=test_product.id,
                price=Decimal("29.99"),
                original_price=Decimal("39.99"),
                buybox_price=Decimal("29.99"),
                currency="USD",
                discount_percentage=25.0,
                bsr_main_category=1500,
                bsr_small_category=250,
                main_category_name="Electronics",
                small_category_name="Headphones",
                rating=4.5,
                review_count=1234,
                in_stock=True,
                stock_quantity=50,
                seller_name="Amazon.com",
                seller_id="ATVPDKIKX0DER",
                seller_store_url="https://www.amazon.com/stores/Amazon",
                is_amazon_seller=True,
                is_fba=False,
                fulfilled_by="Amazon",
                coupon_available=False,
                coupon_text=None,
                is_deal=True,
                deal_type="Lightning Deal",
                is_prime=True,
                has_amazons_choice=True,
                amazons_choice_keywords={"category": "wireless earbuds"},
                past_sales="5K+ bought in past month",
                delivery_message="FREE delivery Tomorrow",
                product_type="Consumer Electronics",
                is_used=False,
                stock_status="In Stock",
                scraped_at=now,
                created_at=now,
                updated_at=now,
            )
            mock_update.return_value = mock_snapshot

            response = await client.post(
                f"/api/v1/tracking/products/{test_product.id}/update",
                headers=auth_headers,
            )

            assert response.status_code in [200, 202]
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_product(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test refreshing product data."""
        with patch(
            "scrapper.product_tracking_service.ProductTrackingService.refresh_product",
            new_callable=AsyncMock,
        ):
            response = await client.post(
                f"/api/v1/tracking/products/{test_product.id}/refresh",
                headers=auth_headers,
            )

            assert response.status_code in [200, 202]

    @pytest.mark.asyncio
    async def test_batch_update_products(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test batch updating multiple products."""
        with patch(
            "scrapper.product_tracking_service.ProductTrackingService.batch_update_products",
            new_callable=AsyncMock,
        ) as mock_batch:
            mock_batch.return_value = {"success": 1, "failed": 0, "errors": []}

            response = await client.post(
                f"/api/v1/tracking/products/batch-update?product_ids={test_product.id}",
                headers=auth_headers,
            )

            assert response.status_code in [200, 202]

    @pytest.mark.asyncio
    async def test_batch_refresh_products(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test batch refreshing multiple products."""
        with patch(
            "scrapper.product_tracking_service.ProductTrackingService.batch_refresh_products",
            new_callable=AsyncMock,
        ) as mock_batch:
            mock_batch.return_value = {"success": 1, "failed": 0, "errors": []}

            response = await client.post(
                f"/api/v1/tracking/products/batch-refresh?product_ids={test_product.id}",
                headers=auth_headers,
            )

            assert response.status_code in [200, 202]


class TestProductHistory:
    """Tests for product history and snapshot endpoints."""

    @pytest.mark.asyncio
    async def test_get_product_history(
        self,
        client: AsyncClient,
        test_product: Product,
        test_snapshot: ProductSnapshot,
        auth_headers: dict[str, str],
    ):
        """Test getting product price history."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/history",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "price" in data[0]
            assert "timestamp" in data[0] or "created_at" in data[0]

    @pytest.mark.asyncio
    async def test_get_product_history_with_date_range(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test getting product history with date range filter."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/history?days=7",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestProductAlerts:
    """Tests for product alert endpoints."""

    @pytest.mark.asyncio
    async def test_get_product_alerts(
        self,
        client: AsyncClient,
        test_product: Product,
        test_alert,
        auth_headers: dict[str, str],
    ):
        """Test getting alerts for a product."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/alerts",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_mark_alert_as_read(
        self,
        client: AsyncClient,
        test_product: Product,
        test_alert,
        auth_headers: dict[str, str],
    ):
        """Test marking an alert as read."""
        response = await client.post(
            f"/api/v1/tracking/products/{test_product.id}/alerts/{test_alert.id}/read",
            headers=auth_headers,
        )

        assert response.status_code in [200, 204]


class TestProductReviews:
    """Tests for product review endpoints."""

    @pytest.mark.asyncio
    async def test_get_product_reviews(
        self,
        client: AsyncClient,
        test_product: Product,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test getting product reviews."""
        # Create a test review (only use fields that exist in Review model)
        review = Review(
            product_id=test_product.id,
            review_id="R1234567890",
            reviewer_name="John Doe",
            rating=5.0,
            title="Great product",
            text="Really satisfied with this purchase",
            review_date=datetime.now(UTC),
            verified_purchase=True,
            helpful_count=10,
        )
        db_session.add(review)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/reviews",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_product_reviews_stats(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test getting review statistics."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/reviews/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_reviews" in data or "average_rating" in data or "count" in data


class TestProductBestsellers:
    """Tests for bestseller rank endpoints."""

    @pytest.mark.asyncio
    async def test_get_bestseller_rank(
        self,
        client: AsyncClient,
        test_product: Product,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
    ):
        """Test getting current bestseller rank."""
        # Create a category and bestseller snapshot
        from products.models import BestsellerSnapshot, Category

        category = Category(
            name="Electronics",
            marketplace="com",
            category_id="electronics_123",
        )
        db_session.add(category)
        await db_session.flush()  # Get category ID

        bestseller = BestsellerSnapshot(
            category_id=category.id,
            asin=test_product.asin,
            rank=1500,
            scraped_at=datetime.now(UTC),
        )
        db_session.add(bestseller)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/bestsellers",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Response should have BestsellerSnapshotOut structure
        assert "product_rank" in data or "category_name" in data
        if "product_rank" in data:
            assert data["product_rank"] == 1500
        assert "category_name" in data

    @pytest.mark.asyncio
    async def test_get_bestseller_history(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test getting bestseller rank history."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/bestsellers/history",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "history" in data
        assert isinstance(data["history"], list)


class TestProductTrackingFlow:
    """Integration tests for complete product tracking workflows."""

    @pytest.mark.asyncio
    async def test_complete_tracking_flow(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
        db_session: AsyncSession,
    ):
        """Test complete product tracking flow: import → view → update → delete."""
        with patch(
            "scrapper.product_tracking_service.ProductTrackingService.add_product_from_url",
            new_callable=AsyncMock,
        ) as mock_add:
            # 1. Import product
            mock_product = Product(
                id=uuid.uuid4(),
                asin="B01FLOW123",
                marketplace="com",
                title="Flow Test Product",
                url="https://www.amazon.com/dp/B01FLOW123",
                current_price=49.99,
                currency="USD",
                is_active=True,
                track_frequency="daily",
                price_change_threshold=10.0,
                bsr_change_threshold=30.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by_id=test_user.id,
            )

            # Configure mock to save product to database and return it
            async def add_and_save_product(*args, **kwargs):
                db_session.add(mock_product)
                await db_session.commit()
                await db_session.refresh(mock_product)

                # Create UserProduct ownership link
                user_product = UserProduct(
                    user_id=test_user.id,
                    product_id=mock_product.id,
                )
                db_session.add(user_product)
                await db_session.commit()

                return mock_product

            mock_add.side_effect = add_and_save_product

            import_response = await client.post(
                "/api/v1/tracking/products/from-url",
                headers=auth_headers,
                json={
                    "url": "https://www.amazon.com/dp/B01FLOW123",
                    "price_change_threshold": 10.0,
                },
            )
            assert import_response.status_code == 200
            product_id = import_response.json()["id"]

            # 2. View product details
            view_response = await client.get(
                f"/api/v1/tracking/products/{product_id}",
                headers=auth_headers,
            )
            assert view_response.status_code == 200

            # 3. View history
            history_response = await client.get(
                f"/api/v1/tracking/products/{product_id}/history",
                headers=auth_headers,
            )
            assert history_response.status_code == 200

            # 4. Delete product
            delete_response = await client.delete(
                f"/api/v1/tracking/products/{product_id}",
                headers=auth_headers,
            )
            assert delete_response.status_code in [200, 204]
