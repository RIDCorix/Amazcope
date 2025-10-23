"""Simple, focused tests for user-product ownership.

Replaces test_user_products_comprehensive.py with cleaner tests.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from products.models import Product
from users.models import User


class TestProductOwnership:
    """Test product ownership operations."""

    @pytest.mark.asyncio
    async def test_claim_product_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test claiming a product."""
        # Create unowned product
        product = Product(
            asin="B01UNCLAIM",
            marketplace="com",
            title="Unowned Product",
            url="https://www.amazon.com/dp/B01UNCLAIM",
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        response = await client.post(
            "/api/v1/user-products/claim",
            headers=auth_headers,
            json={"product_id": str(product.id)},
        )

        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_list_owned_products(
        self,
        client: AsyncClient,
        test_product: Product,
        auth_headers: dict[str, str],
    ):
        """Test listing user's owned products."""
        response = await client.get(
            "/api/v1/user-products/owned",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)


class TestProductCompetitors:
    """Test competitor tracking."""

    @pytest.mark.asyncio
    async def test_list_competitor_products(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test listing competitor products."""
        response = await client.get(
            "/api/v1/user-products/competitors",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
