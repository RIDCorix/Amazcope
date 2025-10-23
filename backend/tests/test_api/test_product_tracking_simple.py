"""Simple, focused tests for product tracking API.

Replaces test_product_tracking_comprehensive.py with cleaner, more maintainable tests.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from products.models import Product, ProductSnapshot, UserProduct
from users.models import User


class TestProductBasics:
    """Basic product operations."""

    @pytest.mark.asyncio
    async def test_get_product_success(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test getting product details."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["asin"] == test_product.asin
        assert data["title"] == test_product.title

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test getting non-existent product."""
        from uuid import uuid4

        response = await client.get(
            f"/api/v1/tracking/products/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_products(
        self,
        client: AsyncClient,
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

    @pytest.mark.asyncio
    async def test_delete_product(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test deleting a product."""
        response = await client.delete(
            f"/api/v1/tracking/products/{test_product.id}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 204]


class TestProductSnapshots:
    """Test product snapshot/history endpoints."""

    @pytest.mark.asyncio
    async def test_get_product_history(
        self,
        client: AsyncClient,
        test_product: Product,
        test_snapshot: ProductSnapshot,
        auth_headers: dict[str, str],
    ):
        """Test getting product price/BSR history."""
        response = await client.get(
            f"/api/v1/tracking/products/{test_product.id}/history",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)


class TestProductAuth:
    """Test authentication and authorization."""

    @pytest.mark.asyncio
    async def test_requires_authentication(self, client: AsyncClient, test_product: Product):
        """Test that endpoints require authentication."""
        response = await client.get(f"/api/v1/tracking/products/{test_product.id}")

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_user_cannot_access_others_product(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test user cannot access product they don't own."""
        # Create another user's product
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
            title="Other Product",
            url="https://www.amazon.com/dp/B01OTHER12",
        )
        db_session.add(other_product)
        await db_session.commit()
        await db_session.refresh(other_product)

        # Link to other user
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
