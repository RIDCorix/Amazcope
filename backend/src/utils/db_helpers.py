"""Database query helpers for product tasks."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database import get_async_db_context
from products.models import Product, ProductSnapshot
from users.models import User

logger = logging.getLogger(__name__)


async def get_active_products(
    limit: int | None = None, updated_since_days: int = 7, user_id: int | None = None
) -> list[Product]:
    """Get active products updated within specified days.

    Args:
        limit: Maximum number of products to return
        updated_since_days: Only return products updated within this many days
        user_id: Filter products by specific user (optional)

    Returns:
        List of active Product objects with snapshots loaded
    """
    cutoff_date = datetime.utcnow() - timedelta(days=updated_since_days)

    async with get_async_db_context() as db:
        query = (
            select(Product)
            .where(
                Product.is_active,
                Product.updated_at >= cutoff_date,
            )
            .options(selectinload(Product.snapshots))
        )

        if user_id:
            query = query.where(Product.created_by_id == user_id)

        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())


async def get_all_active_users() -> list[User]:
    """Get all users who have active products.

    Returns:
        List of User objects who own at least one active product
    """
    async with get_async_db_context() as db:
        # Get users who have at least one active product
        query = select(User).join(Product).where(Product.is_active).distinct()

        result = await db.execute(query)
        return list(result.scalars().all())


async def get_recent_snapshots(
    product_id: int, limit: int = 10, days_back: int = 7
) -> list[ProductSnapshot]:
    """Get recent snapshots for a product.

    Args:
        product_id: ID of the product
        limit: Maximum number of snapshots to return
        days_back: Only return snapshots from this many days back

    Returns:
        List of ProductSnapshot objects ordered by scraped_at desc
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

    async with get_async_db_context() as db:
        result = await db.execute(
            select(ProductSnapshot)
            .where(
                ProductSnapshot.product_id == product_id,
                ProductSnapshot.scraped_at >= cutoff_date,
            )
            .order_by(ProductSnapshot.scraped_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_products_by_ids(product_ids: list[int]) -> list[Product]:
    """Get products by their IDs.

    Args:
        product_ids: List of product IDs to fetch

    Returns:
        List of Product objects
    """
    if not product_ids:
        return []

    async with get_async_db_context() as db:
        result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        return list(result.scalars().all())


async def batch_update_product_timestamps(product_ids: list[int]) -> None:
    """Update the updated_at timestamp for multiple products.

    Args:
        product_ids: List of product IDs to update
    """
    if not product_ids:
        return

    async with get_async_db_context() as db:
        # Update timestamps for processed products
        from sqlalchemy import update

        stmt = (
            update(Product).where(Product.id.in_(product_ids)).values(updated_at=datetime.utcnow())
        )
        await db.execute(stmt)
        await db.commit()
        logger.info(f"Updated timestamps for {len(product_ids)} products")


async def get_user_product_count(user_id: int) -> int:
    """Get count of active products for a user.

    Args:
        user_id: ID of the user

    Returns:
        Number of active products owned by the user
    """
    async with get_async_db_context() as db:
        result = await db.execute(
            select(Product.id).where(Product.created_by_id == user_id, Product.is_active)
        )
        return len(result.scalars().all())
