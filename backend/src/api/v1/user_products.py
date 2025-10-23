"""API endpoints for product ownership management (UserProduct)."""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, get_current_user
from products.models import (
    Product,
    ProductSnapshot,
    UserProduct,
)
from schemas.user_product import (
    ClaimProductResponse,
    CompetitorProductList,
    ProductWithOwnershipOut,
    UserProductCreate,
    UserProductOut,
    UserProductUpdate,
)
from users.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/claim", response_model=ClaimProductResponse, status_code=status.HTTP_201_CREATED)
async def claim_product(
    data: UserProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Claim ownership of a product.

    This allows users to:
    - Claim competitor products discovered via bestseller scraping
    - Mark products they own/sell on Amazon
    - Set custom tracking thresholds

    Args:
        data: Product claiming data
        current_user: Current authenticated user

    Returns:
        Claim confirmation with UserProduct details

    Raises:
        404: Product not found
        400: Product already claimed by this user
    """
    # Check if product exists
    result = await db.execute(select(Product).where(Product.id == data.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {data.product_id} not found",
        )

    # Check if user already owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == current_user.id,
            UserProduct.product_id == data.product_id,
        )
    )
    existing_ownership = result.scalar_one_or_none()
    if existing_ownership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already own this product",
        )

    # Create ownership record
    user_product = UserProduct(
        user_id=current_user.id,
        product_id=data.product_id,
        is_primary=data.is_primary,
        price_change_threshold=data.price_change_threshold,
        bsr_change_threshold=data.bsr_change_threshold,
        notes=data.notes,
    )
    db.add(user_product)

    # Mark product as no longer a competitor (user owns it)
    product.is_competitor = False
    product.is_active = True  # Activate tracking when claimed
    await db.commit()
    await db.refresh(user_product)

    logger.info(f"User {current_user.id} claimed product {product.asin} (ID: {product.id})")

    return ClaimProductResponse(
        success=True,
        message=f"Successfully claimed product: {product.title}",
        user_product=UserProductOut.model_validate(user_product),
        product_id=product.id,
        asin=product.asin,
    )


@router.delete("/{product_id}/unclaim", status_code=status.HTTP_204_NO_CONTENT)
async def unclaim_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """Unclaim/release ownership of a product.

    Args:
        product_id: Product ID to unclaim
        current_user: Current authenticated user

    Raises:
        404: Product not owned by user
    """
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == current_user.id,
            UserProduct.product_id == product_id,
        )
    )
    user_product = result.scalar_one_or_none()
    if not user_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't own this product",
        )

    await db.delete(user_product)
    await db.commit()

    # Check if any other users own this product
    result = await db.execute(
        select(func.count()).select_from(UserProduct).where(UserProduct.product_id == product_id)
    )
    other_owners = result.scalar()
    if other_owners == 0:
        # No other owners - mark as competitor again
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one()
        product.is_competitor = True
        product.is_active = False  # Deactivate tracking
        await db.commit()

    logger.info(f"User {current_user.id} unclaimed product {product_id}")


@router.get("/owned", response_model=list[UserProductOut])
async def get_owned_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get all products owned by the current user.

    Args:
        current_user: Current authenticated user

    Returns:
        List of owned products
    """
    result = await db.execute(select(UserProduct).where(UserProduct.user_id == current_user.id))
    owned_products = result.scalars().all()
    return [UserProductOut.model_validate(up) for up in owned_products]


@router.get("/competitors", response_model=CompetitorProductList)
async def get_competitor_products(
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get competitor products (not owned by user) with ownership info.

    This endpoint shows all products in the system with flags indicating
    which ones the user owns.

    Args:
        category: Filter by category (optional)
        limit: Maximum products to return
        offset: Pagination offset
        current_user: Current authenticated user

    Returns:
        List of products with ownership information
    """
    # Build query
    query = select(Product)
    if category:
        query = query.where(Product.category.ilike(f"%{category}%"))

    # Get products
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    products = result.scalars().all()
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total_count = result.scalar()

    # Get user's owned product IDs
    result = await db.execute(
        select(UserProduct.product_id).where(UserProduct.user_id == current_user.id)
    )
    owned_product_ids = result.scalars().all()
    owned_product_ids_set: set[UUID] = set(owned_product_ids)  # type: ignore[arg-type]

    # Build response with ownership info
    result_products = []
    for product in products:
        is_owned = product.id in owned_product_ids_set

        # Get ownership record if owned
        ownership = None
        if is_owned:
            result = await db.execute(
                select(UserProduct).where(
                    UserProduct.user_id == current_user.id,
                    UserProduct.product_id == product.id,
                )
            )
            user_product = result.scalar_one_or_none()
            if user_product:
                ownership = UserProductOut.model_validate(user_product)

        # Get latest snapshot data
        result = await db.execute(
            select(ProductSnapshot)
            .where(ProductSnapshot.product_id == product.id)
            .order_by(ProductSnapshot.scraped_at.desc())
            .limit(1)
        )
        latest_snapshot = result.scalar_one_or_none()

        result_products.append(
            ProductWithOwnershipOut(
                id=product.id,
                asin=product.asin,
                title=product.title,
                brand=product.brand,
                category=product.category,
                url=product.url,
                image_url=product.image_url,
                is_competitor=product.is_competitor,
                is_active=product.is_active,
                is_owned=is_owned,
                ownership=ownership,
                latest_price=float(latest_snapshot.price)
                if latest_snapshot and latest_snapshot.price
                else None,
                latest_bsr=latest_snapshot.bsr_main_category if latest_snapshot else None,
                latest_rating=latest_snapshot.rating if latest_snapshot else None,
            )
        )

    owned_count = len([p for p in result_products if p.is_owned])
    competitor_count = len([p for p in result_products if not p.is_owned])

    return CompetitorProductList(
        total=total_count,
        owned_count=owned_count,
        competitor_count=competitor_count,
        products=result_products,
    )


@router.put("/{product_id}", response_model=UserProductOut)
async def update_owned_product(
    product_id: UUID,
    data: UserProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Update ownership settings for a product.

    Args:
        product_id: Product ID
        data: Update data
        current_user: Current authenticated user

    Returns:
        Updated UserProduct

    Raises:
        404: Product not owned by user
    """
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == current_user.id,
            UserProduct.product_id == product_id,
        )
    )
    user_product = result.scalar_one_or_none()
    if not user_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't own this product",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user_product, field, value)

    await db.commit()
    await db.refresh(user_product)

    logger.info(f"User {current_user.id} updated ownership for product {product_id}")

    return UserProductOut.model_validate(user_product)


@router.get("/{product_id}", response_model=UserProductOut)
async def get_owned_product_details(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Get ownership details for a specific product.

    Args:
        product_id: Product ID
        current_user: Current authenticated user

    Returns:
        UserProduct details

    Raises:
        404: Product not owned by user
    """
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == current_user.id,
            UserProduct.product_id == product_id,
        )
    )
    user_product = result.scalar_one_or_none()
    if not user_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't own this product",
        )

    return UserProductOut.model_validate(user_product)
