"""Expanded tests for product tracking API endpoints.

Tests additional endpoints not covered in test_product_tracking_simple.py:
- Add product from URL
- Update product information
- Update category
- Update user settings
- Refresh product data
- Get alerts
- Reviews and stats
- Batch operations
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from alert.models import Alert
from products.models import Product, ProductSnapshot, Review, UserProduct
from users.models import User


@pytest.mark.asyncio
class TestAddProductFromUrl:
    """Test POST /api/v1/tracking/products/from-url endpoint."""

    async def test_add_product_from_url_success(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test adding a new product from Amazon URL."""
        with patch(
            "scrapper.product_tracking_service.ProductTrackingService.add_product_from_url"
        ) as mock_add:
            # Mock the service to return a product
            mock_product = Product(
                id=uuid4(),
                asin="B07XJ8C8F5",
                marketplace="com",
                title="Test Product from URL",
                url="https://www.amazon.com/dp/B07XJ8C8F5",
                created_by_id=test_user.id,
                is_active=True,
                track_frequency="daily",
                price_change_threshold=10.0,
                bsr_change_threshold=30.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            mock_add.return_value = mock_product

            response = await client.post(
                "/api/v1/tracking/products/from-url",
                headers=auth_headers,
                json={
                    "url": "https://www.amazon.com/dp/B07XJ8C8F5",
                    "price_change_threshold": 10.0,
                    "bsr_change_threshold": 30.0,
                    "scrape_reviews": True,
                    "scrape_bestsellers": False,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["asin"] == "B07XJ8C8F5"

    async def test_add_product_from_url_validation_error(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test validation error with invalid URL."""
        response = await client.post(
            "/api/v1/tracking/products/from-url",
            headers=auth_headers,
            json={
                "url": "not-a-valid-url",
                "price_change_threshold": 10.0,
                "bsr_change_threshold": 30.0,
            },
        )

        # FastAPI validation returns 422
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestUpdateProduct:
    """Test PUT /api/v1/tracking/products/{id} endpoint."""

    async def test_update_product_success(
        self, client: AsyncClient, test_product: Product, auth_headers: dict
    ):
        """Test updating product information."""
        response = await client.put(
            f"/api/v1/tracking/products/{test_product.id}",
            headers=auth_headers,
            json={
                "title": "Updated Product Title",
                "brand": "Updated Brand",
                "is_active": True,
                "price_change_threshold": 15.0,
                "bsr_change_threshold": 25.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Product Title"

    async def test_update_nonexistent_product(self, client: AsyncClient, auth_headers: dict):
        """Test updating non-existent product."""
        fake_id = uuid4()
        response = await client.put(
            f"/api/v1/tracking/products/{fake_id}",
            headers=auth_headers,
            json={"title": "New Title"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestPatchCategory:
    """Test PATCH /api/v1/tracking/products/{id}/category endpoint."""

    async def test_patch_category_success(
        self, client: AsyncClient, test_product: Product, auth_headers: dict
    ):
        """Test updating product category."""
        response = await client.patch(
            f"/api/v1/tracking/products/{test_product.id}/category",
            headers=auth_headers,
            json={
                "category": "Electronics",
                "small_category": "Smartphones",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "category" in data or "asin" in data


@pytest.mark.asyncio
class TestUpdateUserSettings:
    """Test PATCH /api/v1/tracking/products/{id}/user-settings endpoint."""

    async def test_update_user_settings_success(
        self, client: AsyncClient, test_product: Product, auth_headers: dict
    ):
        """Test updating user-specific product settings."""
        response = await client.patch(
            f"/api/v1/tracking/products/{test_product.id}/user-settings",
            headers=auth_headers,
            json={
                "price_change_threshold": 12.5,
                "bsr_change_threshold": 35.0,
                "notes": "Test notes",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") or "price_change_threshold" in data


@pytest.mark.asyncio
class TestUpdateProductSnapshot:
    """Test POST /api/v1/tracking/products/{id}/update endpoint."""

    async def test_trigger_update_success(
        self, client: AsyncClient, test_product: Product, auth_headers: dict
    ):
        """Test triggering product snapshot update."""
        from datetime import UTC

        with patch(
            "scrapper.product_tracking_service.ProductTrackingService.update_product"
        ) as mock_update:
            # Create complete mock snapshot with all required fields
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
                review_count=250,
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

            assert response.status_code in [200, 201]
            mock_update.assert_called_once()


@pytest.mark.asyncio
class TestRefreshProduct:
    """Test POST /api/v1/tracking/products/{id}/refresh endpoint."""

    async def test_refresh_product_success(
        self, client: AsyncClient, test_product: Product, auth_headers: dict
    ):
        """Test refreshing product data (triggers scraping)."""
        with patch(
            "scrapper.product_tracking_service.ProductTrackingService.refresh_product"
        ) as mock_refresh:
            mock_refresh.return_value = test_product

            response = await client.post(
                f"/api/v1/tracking/products/{test_product.id}/refresh",
                headers=auth_headers,
            )

            assert response.status_code == 200


@pytest.mark.asyncio
class TestGetProductAlerts:
    """Test GET /api/v1/tracking/products/{id}/alerts endpoint."""

    async def test_get_alerts_success(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict,
        db_session,
        test_user: User,
    ):
        """Test getting product alerts."""
        # Create test alerts
        alert1 = Alert(
            title="Price Drop Alert",
            product_id=test_product.id,
            user_id=test_user.id,
            alert_type="price_change",
            message="Price dropped by 15%",
            severity="medium",
            is_read=False,
        )
        alert2 = Alert(
            title="BSR Improvement Alert",
            product_id=test_product.id,
            user_id=test_user.id,
            alert_type="bsr_change",
            message="BSR improved by 40%",
            severity="high",
            is_read=False,
        )
        db_session.add_all([alert1, alert2])
        await db_session.commit()

        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/alerts",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_get_alerts_with_filters(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict,
        db_session,
        test_user: User,
    ):
        """Test getting alerts with unread filter."""
        alert = Alert(
            title="Stock Change Alert",
            product_id=test_product.id,
            user_id=test_user.id,
            alert_type="stock_change",
            message="Product back in stock",
            severity="low",
            is_read=False,
        )
        db_session.add(alert)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/alerts?unread_only=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
class TestMarkAlertRead:
    """Test POST /api/v1/tracking/products/{id}/alerts/{alert_id}/read endpoint."""

    async def test_mark_alert_read(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict,
        db_session,
        test_user: User,
    ):
        """Test marking an alert as read."""
        alert = Alert(
            title="Test Alert",
            product_id=test_product.id,
            user_id=test_user.id,
            alert_type="price_change",
            message="Test alert",
            severity="medium",
            is_read=False,
        )
        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)

        response = await client.post(
            f"/api/v1/tracking/products/{test_product.id}/alerts/{alert.id}/read",
            headers=auth_headers,
        )

        assert response.status_code == 200


@pytest.mark.asyncio
class TestBatchOperations:
    """Test batch update/refresh endpoints."""

    async def test_batch_update(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict,
        db_session,
        test_user: User,
    ):
        """Test batch updating multiple products."""
        # Create additional products
        product2 = Product(
            asin="B07XJ8C8F6",
            marketplace="com",
            title="Test Product 2",
            url="https://www.amazon.com/dp/B07XJ8C8F6",
        )
        db_session.add(product2)
        await db_session.commit()
        await db_session.refresh(product2)

        user_product = UserProduct(
            user_id=test_user.id,
            product_id=product2.id,
            is_primary=True,
        )
        db_session.add(user_product)
        await db_session.commit()
        await db_session.refresh(user_product)

        with patch(
            "scrapper.product_tracking_service.ProductTrackingService._create_snapshot"
        ) as mock_snap:
            mock_snap.return_value = ProductSnapshot(
                id=uuid4(),
                product_id=test_product.id,
                price=Decimal("29.99"),
                bsr_main_category=1500,
                rating=4.5,
                in_stock=True,
                scraped_at=datetime.utcnow(),
            )

            response = await client.post(
                "/api/v1/tracking/products/batch-update",
                headers=auth_headers,
                json=[str(test_product.id), str(product2.id)],
            )

            # Batch operations may return different status codes
            assert response.status_code in [200, 202, 207]

    async def test_batch_refresh(
        self, client: AsyncClient, test_product: Product, auth_headers: dict
    ):
        """Test batch refreshing multiple products."""
        response = await client.post(
            f"/api/v1/tracking/products/batch-refresh?product_ids={str(test_product.id)}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 202, 207]


@pytest.mark.asyncio
class TestProductReviews:
    """Test product reviews endpoints."""

    async def test_get_reviews(
        self, client: AsyncClient, test_product: Product, auth_headers: dict, db_session
    ):
        """Test getting product reviews."""
        # Create test reviews
        review1 = Review(
            product_id=test_product.id,
            review_id="R1TEST123",
            reviewer_name="Test Reviewer",
            rating=5,
            title="Great product!",
            text="This product is excellent.",
            verified_purchase=True,
            review_date=datetime.utcnow() - timedelta(days=5),
        )
        review2 = Review(
            product_id=test_product.id,
            review_id="R2TEST456",
            reviewer_name="Another Reviewer",
            rating=4,
            title="Good product",
            text="Works well.",
            verified_purchase=True,
            review_date=datetime.utcnow() - timedelta(days=10),
        )
        db_session.add_all([review1, review2])
        await db_session.commit()

        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/reviews",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_get_reviews_with_filters(
        self, client: AsyncClient, test_product: Product, auth_headers: dict, db_session
    ):
        """Test getting reviews with rating filter."""
        review = Review(
            product_id=test_product.id,
            review_id="R3TEST789",
            reviewer_name="5-Star Reviewer",
            rating=5,
            title="Perfect!",
            text="Absolutely perfect product.",
            verified_purchase=True,
            review_date=datetime.utcnow(),
        )
        db_session.add(review)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/reviews?min_rating=5",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_review_stats(
        self, client: AsyncClient, test_product: Product, auth_headers: dict, db_session
    ):
        """Test getting review statistics."""
        reviews = [
            Review(
                product_id=test_product.id,
                review_id=f"R{i}STAT",
                reviewer_name=f"Reviewer {i}",
                rating=rating,
                title=f"Review {i}",
                text="Review text",
                verified_purchase=True,
                review_date=datetime.utcnow(),
            )
            for i, rating in enumerate([5, 5, 4, 4, 3], 1)
        ]
        db_session.add_all(reviews)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/reviews/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "average_rating" in data or "total_reviews" in data


@pytest.mark.asyncio
class TestProductBestsellers:
    """Test bestseller endpoints."""

    async def test_get_bestsellers(
        self, client: AsyncClient, test_product: Product, auth_headers: dict
    ):
        """Test getting bestseller data."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/bestsellers",
            headers=auth_headers,
        )

        # May return 200 with data or 404 if no bestseller data exists
        assert response.status_code in [200, 404]

    async def test_get_bestsellers_history(
        self, client: AsyncClient, test_product: Product, auth_headers: dict
    ):
        """Test getting bestseller history."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/bestsellers/history",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestContentUpdate:
    """Test PATCH /api/v1/tracking/products/{id}/content endpoint."""

    async def test_update_content_success(
        self, client: AsyncClient, test_product: Product, auth_headers: dict
    ):
        """Test updating product content fields."""
        response = await client.patch(
            f"/api/v1/tracking/products/{test_product.id}/content",
            headers=auth_headers,
            json={
                "product_description": "Updated description",
                "features": ["Feature 1", "Feature 2", "Feature 3"],
            },
        )

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestProductTrackingErrors:
    """Test error handling in product tracking endpoints."""

    async def test_unauthorized_access(self, client: AsyncClient, test_product: Product):
        """Test accessing endpoints without authentication."""
        endpoints = [
            f"/api/v1/tracking/products/{test_product.id}",
            "/api/v1/tracking/products",
            f"/api/v1/tracking/products/{test_product.id}/history",
            f"/api/v1/tracking/products/{test_product.id}/alerts",
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code in [401, 403]

    async def test_invalid_product_id_format(self, client: AsyncClient, auth_headers: dict):
        """Test using invalid UUID format."""
        response = await client.get(
            "/api/v1/tracking/products/invalid-uuid",
            headers=auth_headers,
        )

        assert response.status_code == 422
