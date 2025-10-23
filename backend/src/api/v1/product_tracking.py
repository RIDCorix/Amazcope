"""Product tracking API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from alert.models import Alert
from api.deps import get_async_db, get_current_user
from products.models import (
    BestsellerSnapshot,
    Product,
    ProductSnapshot,
    Review,
    UserProduct,
)
from schemas.product_tracking import (
    AlertOut,
    BestsellerSnapshotOut,
    ProductContentUpdate,
    ProductDetailOut,
    ProductFromUrlCreate,
    ProductListOut,
    ProductOut,
    ProductUpdate,
    ProductUpdateCategory,
    ReviewOut,
    SnapshotOut,
    UserProductUpdate,
)
from scrapper.product_tracking_service import ProductTrackingService
from users.models import User

if TYPE_CHECKING:
    from products.models import BestsellerSnapshot
router = APIRouter()


@router.post("/products/from-url", response_model=ProductOut)
async def add_product_from_url(
    product_in: ProductFromUrlCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Product:
    """Add a new product to track from Amazon URL.

    This endpoint:
    1. Extracts ASIN from the provided Amazon URL
    2. Creates product record with basic information
    3. Launches 3 background jobs:
       - Scrape detailed product information
       - Scrape product reviews (if enabled)
       - Scrape category bestsellers (if enabled)

    Args:
        product_in: Product creation data with Amazon URL
        user: Current authenticated user

    Returns:
        Created product with basic information

    Raises:
        HTTPException: If URL is invalid, ASIN extraction fails, or product already tracked
    """
    service = ProductTrackingService(db)

    product = await service.add_product_from_url(
        user_id=user.id,
        amazon_url=product_in.url,
        price_threshold=product_in.price_change_threshold,
        bsr_threshold=product_in.bsr_change_threshold,
        scrape_reviews=product_in.scrape_reviews,
        scrape_bestsellers=product_in.scrape_bestsellers,
        category_url=product_in.category_url,
        manual_category=product_in.manual_category,
        manual_small_category=product_in.manual_small_category,
    )
    return product


@router.get("/products", response_model=list[ProductListOut])
async def list_products(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    active_only: bool = Query(True, description="Only return active products"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """List all products tracked by the current user with latest snapshot data.

    Args:
        user: Current authenticated user
        active_only: Filter by active status
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of products with latest snapshot data (price, rating, stock, etc.)
    """
    # Get product IDs owned by user
    result = await db.execute(select(UserProduct).where(UserProduct.user_id == user.id))
    user_products = result.scalars().all()
    product_ids = [up.product_id for up in user_products]

    if not product_ids:
        return []

    # Build query for products - now using denormalized fields for performance
    query = select(Product).where(Product.id.in_(product_ids))

    if active_only:
        query = query.where(Product.is_active == True)  # noqa: E712

    query = query.order_by(Product.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()

    # Get unread alert counts for all products in one query (performance optimization)
    product_ids_in_page = [p.id for p in products]
    from alert.models import Alert

    if product_ids_in_page:
        alerts_query = (
            select(Alert.product_id, func.count(Alert.id).label("count"))
            .where(Alert.product_id.in_(product_ids_in_page), Alert.is_read == False)  # noqa: E712
            .group_by(Alert.product_id)
        )
        alerts_result = await db.execute(alerts_query)
        alerts_map = {row[0]: row[1] for row in alerts_result.all()}
    else:
        alerts_map = {}

    # Convert to response model - no need for complex joins anymore!
    products_list = []
    for product in products:
        product_dict = {
            "id": product.id,
            "asin": product.asin,
            "title": product.title,
            "brand": product.brand,
            "category": product.category,
            "url": product.url,
            "image_url": product.image_url,
            "is_active": product.is_active,
            "created_at": product.created_at,
            # Denormalized fields from latest snapshot
            "price": product.current_price,
            "original_price": product.original_price,
            "currency": product.currency,
            "discount_percentage": product.discount_percentage,
            "bsr_main_category": product.current_bsr,
            "rating": product.rating,
            "review_count": product.review_count or 0,
            "in_stock": product.in_stock,
            "stock_status": product.stock_status,
            "is_prime": product.is_prime,
            "scraped_at": product.last_snapshot_at,
            # Alert statistics
            "unread_alerts_count": alerts_map.get(product.id, 0),
        }
        products_list.append(product_dict)

    return products_list


@router.get("/products/{product_id}", response_model=ProductDetailOut)
async def get_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get detailed information about a specific product.

    Args:
        product_id: Product ID
        user: Current authenticated user

    Returns:
        Product details with latest snapshot

    Raises:
        HTTPException: If product not found
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get product with relationships
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.snapshots), selectinload(Product.alerts))
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get latest snapshot
    result = await db.execute(
        select(ProductSnapshot)
        .options(selectinload(ProductSnapshot.product))
        .where(ProductSnapshot.product_id == product_id)
        .order_by(ProductSnapshot.scraped_at.desc())
        .limit(1)
    )
    latest_snapshot = result.scalar_one_or_none()

    # Get unread alert count
    unread_alerts = await db.scalar(
        select(func.count())
        .select_from(Alert)
        .where(Alert.product_id == product.id, Alert.is_read is False)
    )

    return {
        **product.as_dict(),
        "latest_snapshot": latest_snapshot,
        "unread_alerts_count": unread_alerts,
    }


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    hard_delete: bool = False,
) -> None:
    """Delete or deactivate a product.

    Args:
        product_id: Product ID
        user: Current authenticated user
        hard_delete: If True, permanently delete; otherwise just deactivate

    Raises:
        HTTPException: If product not found
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if hard_delete:
        await product.delete()
    else:
        product.is_active = False
        await db.commit()


@router.patch("/products/{product_id}/category", response_model=ProductOut)
async def update_product_category(
    product_id: UUID,
    category_in: ProductUpdateCategory,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Product:
    """Update product category information.

    This endpoint allows you to:
    1. Manually set or override category names
    2. Provide a custom category URL for bestseller tracking
    3. Optionally trigger immediate bestseller scraping

    Args:
        product_id: Product ID
        category_in: Category update data
        user: Current authenticated user

    Returns:
        Updated product

    Raises:
        HTTPException: If product not found or update fails
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    service = ProductTrackingService(db)

    try:
        product = await service.update_product_category(
            product_id=product_id,
            category_url=category_in.category_url,
            manual_category=category_in.manual_category,
            manual_small_category=category_in.manual_small_category,
            trigger_bestsellers_scrape=category_in.trigger_bestsellers_scrape,
        )
        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update category: {str(e)}")


@router.put("/products/{product_id}", response_model=ProductOut)
async def update_product_details(
    product_id: UUID,
    product_update: ProductUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Product:
    """Update product details and settings.

    Allows users to update:
    - Basic product information (title, brand, category)
    - Tracking settings (active status, frequency)
    - Alert thresholds (price and BSR change percentages)
    - Product URLs and metadata
    - Product description and features

    Args:
        product_id: Product ID
        product_update: Product update data
        user: Current authenticated user

    Returns:
        Updated product

    Raises:
        HTTPException: If product not found or update fails
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Product).where(Product.id == product_id))
    product: Product | None = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update product fields
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(product, field):
            setattr(product, field, value)

    db.add(product)
    await db.commit()
    await db.refresh(product)

    return product


@router.patch("/products/{product_id}/user-settings", response_model=dict[str, Any])
async def update_user_product_settings(
    product_id: UUID,
    settings_update: UserProductUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Update user-specific product settings.

    Allows users to update their personal settings for a product:
    - Tracking status (active/inactive for this user)
    - Custom alert thresholds (overrides global product thresholds)
    - Personal notes about the product

    Args:
        product_id: Product ID
        settings_update: User settings update data
        user: Current authenticated user

    Returns:
        Updated user product settings

    Raises:
        HTTPException: If product not found or update fails
    """
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    user_product = result.scalar_one_or_none()
    if not user_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update user product fields
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user_product, field):
            setattr(user_product, field, value)

    db.add(user_product)
    await db.commit()
    await db.refresh(user_product)

    return {
        "product_id": str(product_id),
        "user_id": str(user.id),
        "is_active": user_product.is_active,
        "price_change_threshold": user_product.price_change_threshold,
        "bsr_change_threshold": user_product.bsr_change_threshold,
        "notes": user_product.notes,
        "updated_at": user_product.updated_at,
    }


@router.patch("/products/{product_id}/content", response_model=ProductOut)
async def update_product_content(
    product_id: UUID,
    content_update: ProductContentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Product:
    """Update product content with AI-enhanced descriptions and features.

    This endpoint is designed to work with AI content generation tools
    like CopilotTextarea to help users create better product descriptions,
    marketing copy, and SEO-optimized content.

    Args:
        product_id: Product ID
        content_update: AI-enhanced content data
        user: Current authenticated user

    Returns:
        Updated product with enhanced content

    Raises:
        HTTPException: If product not found or update fails
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Product).where(Product.id == product_id))
    product: Product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update product content fields
    update_data = content_update.model_dump(exclude_unset=True)

    # Handle product description
    if "product_description" in update_data:
        product.product_description = update_data["product_description"]

    # Handle features - convert list to dict format expected by the model
    if "features" in update_data and update_data["features"]:
        product.features = {
            "bullet_points": update_data["features"],
            "generated_by": "ai_assistant",
            "updated_at": datetime.utcnow().isoformat(),
        }

    # Store additional AI-generated content in product_overview
    ai_content = {}
    if "marketing_copy" in update_data:
        ai_content["marketing_copy"] = update_data["marketing_copy"]
    if "seo_keywords" in update_data:
        ai_content["seo_keywords"] = update_data["seo_keywords"]
    if "competitor_analysis" in update_data:
        ai_content["competitor_analysis"] = update_data["competitor_analysis"]

    if ai_content:
        if product.product_overview:
            product.product_overview.update(ai_content)
        else:
            product.product_overview = ai_content

    db.add(product)
    await db.commit()
    await db.refresh(product)

    return product


@router.post("/products/{product_id}/update", response_model=SnapshotOut)
async def update_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> ProductSnapshot:
    """Manually trigger an update for a specific product.

    This uses cached data if available (within 24 hours).
    Use /refresh endpoint for real-time data.

    Args:
        product_id: Product ID
        user: Current authenticated user

    Returns:
        Newly created snapshot

    Raises:
        HTTPException: If product not found or update fails
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    service = ProductTrackingService(db)

    try:
        snapshot = await service.update_product(product_id, check_alerts=True)
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")


@router.post("/products/{product_id}/refresh", response_model=ProductDetailOut)
async def refresh_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    update_metadata: bool = True,
) -> dict[str, Any]:
    """Force real-time refresh from Amazon (bypasses cache).

    This endpoint:
    1. Scrapes fresh data directly from Amazon
    2. Creates new snapshot with latest data
    3. Optionally updates product metadata (title, features, specs, variations)
    4. Checks alert conditions
    5. Returns updated product with new snapshot

    Use this for:
    - Getting real-time pricing/BSR updates
    - Refreshing Amazon's Choice status
    - Updating product variations
    - Checking latest sales velocity

    Args:
        product_id: Product ID
        user: Current authenticated user
        update_metadata: If True, updates product base fields (default: True)

    Returns:
        Updated product details with latest snapshot

    Raises:
        HTTPException: If product not found or refresh fails
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    service = ProductTrackingService(db)

    try:
        # Force fresh scrape (bypass cache)
        await service.refresh_product(
            product_id, update_metadata=update_metadata, check_alerts=True
        )

        # Get updated product with latest data
        await db.refresh(product)
        latest_snapshot = (
            await ProductSnapshot.filter(product=product).order_by("-scraped_at").first()
        )
        unread_alerts = await Alert.filter(product=product, is_read=False).count()

        return {
            **product.__dict__,
            "latest_snapshot": latest_snapshot,
            "unread_alerts_count": unread_alerts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh product: {str(e)}")


@router.get("/products/{product_id}/history", response_model=list[SnapshotOut])
async def get_product_history(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    days: int = Query(30, ge=1, le=365),
) -> list[ProductSnapshot]:
    """Get historical snapshots for a product.

    Args:
        product_id: Product ID
        user: Current authenticated user
        days: Number of days of history to retrieve

    Returns:
        List of snapshots ordered by date (newest first)

    Raises:
        HTTPException: If product not found
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    service = ProductTrackingService(db)
    snapshots = await service.get_product_history(product_id, days)
    return snapshots


@router.get("/products/{product_id}/alerts", response_model=list[AlertOut])
async def get_product_alerts(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    unread_only: bool = Query(False, description="Only return unread alerts"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    """Get alerts for a specific product.

    Args:
        product_id: Product ID
        user: Current authenticated user
        unread_only: Filter by read status
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of alerts ordered by date (newest first)

    Raises:
        HTTPException: If product not found
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = select(Alert).where(Alert.product_id == product.id)

    if unread_only:
        query = query.where(Alert.is_read == False)  # noqa: E712

    query = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()
    return list(alerts)


@router.post("/products/{product_id}/alerts/{alert_id}/read", response_model=AlertOut)
async def mark_alert_read(
    product_id: UUID,
    alert_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Alert:
    """Mark an alert as read.

    Args:
        product_id: Product ID
        alert_id: Alert ID
        user: Current authenticated user

    Returns:
        Updated alert

    Raises:
        HTTPException: If product or alert not found
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    alert_result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.product_id == product.id)
    )
    alert: Alert = alert_result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    await db.commit()
    return alert  # type: ignore[return-value]


@router.post("/products/batch-update")
async def batch_update_products(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    product_ids: list[UUID] | None = None,
) -> dict[str, Any]:
    """Trigger batch update for multiple products (uses cache if available).

    Args:
        user: Current authenticated user
        product_ids: List of product IDs to update (if None, update all active products)

    Returns:
        Update statistics

    Raises:
        HTTPException: If batch update fails
    """
    service = ProductTrackingService(db)

    # If no product IDs specified, get all active products for user
    if product_ids is None:
        result = await db.execute(
            select(UserProduct)
            .options(selectinload(UserProduct.product))
            .where(UserProduct.user_id == user.id)
        )
        user_products = result.scalars().all()
        products = [up.product for up in user_products if up.product and up.product.is_active]
        product_ids = [p.id for p in products]
    else:
        # Verify all products belong to user
        result = await db.execute(
            select(UserProduct.product_id).where(
                UserProduct.user_id == user.id,
                UserProduct.product_id.in_(product_ids),
            )
        )
        user_product_ids = [row for row in result.scalars().all()]
        product_result = await db.execute(select(Product).where(Product.id.in_(user_product_ids)))
        products = list(product_result.scalars().all())
        if len(products) != len(product_ids):
            raise HTTPException(
                status_code=400,
                detail="Some product IDs are invalid or don't belong to you",
            )

    if not product_ids:
        return {"success": 0, "failed": 0, "errors": []}

    try:
        batch_result: dict[str, Any] = await service.batch_update_products(product_ids)
        return batch_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.post("/products/batch-refresh")
async def batch_refresh_products(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    product_ids: list[UUID] | None = None,
    update_metadata: bool = True,
) -> dict[str, Any]:
    """Force real-time refresh for multiple products (bypasses cache).

    This endpoint scrapes fresh data from Amazon for all specified products.
    Use this when you need guaranteed real-time data for multiple products.

    Args:
        user: Current authenticated user
        product_ids: List of product IDs to refresh (if None, refresh all active products)
        update_metadata: If True, updates product base fields for all products

    Returns:
        Refresh statistics with success/failure counts

    Raises:
        HTTPException: If batch refresh fails
    """
    service = ProductTrackingService(db)

    # If no product IDs specified, get all active products for user
    if product_ids is None:
        result = await db.execute(
            select(UserProduct)
            .options(selectinload(UserProduct.product))
            .where(UserProduct.user_id == user.id)
        )
        user_products = result.scalars().all()
        products = [up.product for up in user_products if up.product and up.product.is_active]
        product_ids = [p.id for p in products]
    else:
        # Verify all products belong to user
        result = await db.execute(
            select(UserProduct.product_id).where(
                UserProduct.user_id == user.id,
                UserProduct.product_id.in_(product_ids),
            )
        )
        user_product_ids = [row for row in result.scalars().all()]
        product_result = await db.execute(select(Product).where(Product.id.in_(user_product_ids)))
        products = list(product_result.scalars().all())
        if len(products) != len(product_ids):
            raise HTTPException(
                status_code=400,
                detail="Some product IDs are invalid or don't belong to you",
            )

    if not product_ids:
        return {
            "success": 0,
            "failed": 0,
            "errors": [],
            "note": "No products to refresh",
        }

    try:
        batch_result: dict[str, Any] = await service.batch_refresh_products(
            product_ids,
            update_metadata=update_metadata,  # type: ignore[arg-type]
        )
        return batch_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch refresh failed: {str(e)}")


@router.get("/products/{product_id}/reviews", response_model=list[ReviewOut])
async def get_product_reviews(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    min_rating: float | None = Query(None, ge=1.0, le=5.0, description="Minimum rating filter"),
    verified_only: bool = Query(False, description="Only show verified purchases"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """Get reviews for a specific product.

    Args:
        product_id: Product ID
        user: Current authenticated user
        min_rating: Minimum rating filter (1-5 stars)
        verified_only: Only return verified purchase reviews
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of reviews ordered by date (newest first)

    Raises:
        HTTPException: If product not found
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = select(Review).where(Review.product_id == product.id)

    if min_rating is not None:
        query = query.where(Review.rating >= min_rating)

    if verified_only:
        query = query.where(Review.verified_purchase == True)  # noqa: E712

    query = query.order_by(Review.review_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    reviews = result.scalars().all()

    return list(reviews)


@router.get("/products/{product_id}/reviews/stats")
async def get_product_reviews_stats(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get review statistics for a product.

    Args:
        product_id: Product ID
        user: Current authenticated user

    Returns:
        Review statistics including rating distribution and counts

    Raises:
        HTTPException: If product not found
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = await Review.filter(product=product).all()

    if not reviews:
        return {
            "total_reviews": 0,
            "average_rating": 0,
            "verified_purchases": 0,
            "rating_distribution": {
                "5_star": 0,
                "4_star": 0,
                "3_star": 0,
                "2_star": 0,
                "1_star": 0,
            },
        }

    total = len(reviews)
    average_rating = sum(r.rating for r in reviews) / total
    verified_count = sum(1 for r in reviews if r.verified_purchase)

    # Calculate rating distribution
    rating_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in reviews:
        rating_int = int(review.rating)
        rating_counts[rating_int] = rating_counts.get(rating_int, 0) + 1

    return {
        "total_reviews": total,
        "average_rating": round(average_rating, 2),
        "verified_purchases": verified_count,
        "rating_distribution": {
            "5_star": rating_counts[5],
            "4_star": rating_counts[4],
            "3_star": rating_counts[3],
            "2_star": rating_counts[2],
            "1_star": rating_counts[1],
        },
    }


@router.get("/products/{product_id}/bestsellers", response_model=BestsellerSnapshotOut)
async def get_product_bestsellers(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    latest: bool = Query(True, description="Get only the latest snapshot"),
) -> dict[str, Any] | list[BestsellerSnapshot]:
    """Get category bestsellers snapshot for a product.

    Args:
        product_id: Product ID
        user: Current authenticated user
        latest: If True, return only the latest snapshot

    Returns:
        Bestseller snapshot with category ranking information

    Raises:
        HTTPException: If product not found or no snapshot available
    """
    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = select(BestsellerSnapshot).where(BestsellerSnapshot.product_id == product.id)

    if latest:
        query = query.order_by(BestsellerSnapshot.snapshot_date.desc()).limit(1)
        result = await db.execute(query)
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail="No bestseller snapshot available. Data is being collected in background.",
            )

        # Calculate product's rank in this snapshot
        product_rank = snapshot.get_product_rank(product.asin)

        return {
            **snapshot.__dict__,
            "product_rank": product_rank,
            "top_10": snapshot.get_top_n(10),
        }
    else:
        query = query.order_by(BestsellerSnapshot.snapshot_date.desc())
        result = await db.execute(query)
        snapshots = result.scalars().all()
        if not snapshots:
            raise HTTPException(status_code=404, detail="No bestseller snapshots available")
        return list(snapshots)


@router.get("/products/{product_id}/bestsellers/history")
async def get_bestsellers_history(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch"),
) -> dict[str, Any]:
    """Get historical bestseller ranking for a product.

    Args:
        product_id: Product ID
        user: Current authenticated user
        days: Number of days of history to retrieve

    Returns:
        List of rank changes over time

    Raises:
        HTTPException: If product not found
    """
    from datetime import datetime, timedelta

    # Check if user owns this product
    result = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id, UserProduct.product_id == product_id
        )
    )
    ownership = result.scalar_one_or_none()
    if not ownership:
        raise HTTPException(status_code=404, detail="Product not found")

    product_result = await db.execute(select(Product).where(Product.id == product_id))
    product: Product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    since_date = datetime.utcnow() - timedelta(days=days)

    snapshot_result = await db.execute(
        select(BestsellerSnapshot)
        .where(
            BestsellerSnapshot.product_id == product.id,
            BestsellerSnapshot.snapshot_date >= since_date,
        )
        .order_by(BestsellerSnapshot.snapshot_date)
    )
    snapshots = snapshot_result.scalars().all()

    history = []
    for snapshot in snapshots:
        rank = snapshot.get_product_rank(product.asin)
        if rank:
            history.append(
                {
                    "date": snapshot.snapshot_date,
                    "rank": rank,
                    "category": snapshot.category_name,
                    "total_products": snapshot.total_products_scraped,
                }
            )

    return {"product_asin": product.asin, "history": history}
