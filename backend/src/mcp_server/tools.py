"""MCP Tools for product operations.

Provides function tools that AI agents can call to interact with the
Amazcope product tracking system.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from core.database import get_async_db_context
from mcp_server.server import mcp_server
from optimization.models import (
    ActionStatus,
    ActionType,
    Suggestion,
    SuggestionAction,
    SuggestionCategory,
    SuggestionPriority,
    SuggestionStatus,
)
from products.models import (
    Product,
    ProductSnapshot,
    UserProduct,
)


@mcp_server.tool()
async def get_product_details(product_id: UUID) -> dict[str, Any]:
    """Get detailed information about a specific product.

    Args:
        product_id: The ID of the product to retrieve

    Returns:
        Product details including pricing, BSR, rating, and metadata
    """
    try:
        async with get_async_db_context() as db:
            result = await db.execute(
                select(Product)
                .where(Product.id == product_id)
                .options(
                    selectinload(Product.snapshots),
                    selectinload(Product.alerts),
                    selectinload(Product.reviews),
                )
            )
            product = result.scalar_one_or_none()

            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            # Get latest snapshot
            snapshot_result = await db.execute(
                select(ProductSnapshot)
                .where(ProductSnapshot.product_id == product_id)
                .order_by(ProductSnapshot.scraped_at.desc())
                .limit(1)
            )
            latest_snapshot = snapshot_result.scalar_one_or_none()

            return {
                "id": product.id,
                "asin": product.asin,
                "title": product.title,
                "description": product.description,
                "marketplace": product.marketplace,
                "category": product.category,
                "brand": product.brand,
                "current_price": float(latest_snapshot.price)
                if latest_snapshot and latest_snapshot.price
                else None,
                "currency": latest_snapshot.currency if latest_snapshot else None,
                "current_bsr": latest_snapshot.bsr_main_category if latest_snapshot else None,
                "current_rating": product.rating,
                "review_count": product.review_count,
                "image_url": product.image_url,
                "product_url": product.product_url,
                "is_active": product.is_active,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat(),
            }
    except Exception as e:
        return {"error": f"Failed to retrieve product: {str(e)}"}


@mcp_server.tool()
async def search_products(
    query: str | None = None,
    marketplace: str | None = None,
    category: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search for products based on filters.

    Args:
        query: Search term to filter by title or ASIN
        marketplace: Filter by marketplace (e.g., 'US', 'UK', 'DE')
        category: Filter by product category
        limit: Maximum number of results to return (default: 10)

    Returns:
        List of matching products with basic information
    """
    async with get_async_db_context() as db:
        stmt = select(Product).options(selectinload(Product.user_products))

        if marketplace:
            stmt = stmt.where(Product.marketplace == marketplace)
        if category:
            stmt = stmt.where(Product.category.ilike(f"%{category}%"))
        if query:
            stmt = stmt.where(
                or_(
                    Product.title.ilike(f"%{query}%"),
                    Product.asin.ilike(f"%{query}%"),
                )
            )

        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        products = result.scalars().all()

        return [
            {
                "id": p.id,
                "asin": p.asin,
                "title": p.title,
                "marketplace": p.marketplace,
                "category": p.category,
                "brand": p.brand,
                "rating": p.rating,
                "review_count": p.review_count,
                "is_active": p.is_active,
            }
            for p in products
        ]


@mcp_server.tool()
async def get_price_history(product_id: UUID, days: int = 30) -> dict[str, Any]:
    """Get price history for a product over a specified time period.

    Args:
        product_id: The ID of the product
        days: Number of days of history to retrieve (default: 30)

    Returns:
        Price history data with timestamps and prices
    """
    from datetime import datetime, timedelta

    try:
        async with get_async_db_context() as db:
            # Get product
            product_result = await db.execute(select(Product).where(Product.id == product_id))
            product = product_result.scalar_one_or_none()

            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            cutoff_date = datetime.now() - timedelta(days=days)

            snapshots_result = await db.execute(
                select(ProductSnapshot)
                .where(
                    ProductSnapshot.product_id == product_id,
                    ProductSnapshot.scraped_at >= cutoff_date,
                )
                .order_by(ProductSnapshot.scraped_at)
            )
            snapshots = snapshots_result.scalars().all()

            history = [
                {
                    "timestamp": snap.scraped_at.isoformat(),
                    "price": float(snap.price) if snap.price else None,
                    "currency": snap.currency,
                    "in_stock": snap.in_stock,
                }
                for snap in snapshots
            ]

            # Calculate statistics
            prices: list[float] = [s["price"] for s in history if s["price"] is not None]  # type: ignore[misc]
            stats: dict[str, float] = {}
            if prices:
                stats = {
                    "min_price": min(prices),
                    "max_price": max(prices),
                    "avg_price": sum(prices) / len(prices),
                    "current_price": prices[-1],
                    "price_change": prices[-1] - prices[0] if len(prices) > 1 else 0,
                    "price_change_percent": (
                        ((prices[-1] - prices[0]) / prices[0]) * 100
                        if len(prices) > 1 and prices[0] > 0
                        else 0
                    ),
                }

            return {
                "product_id": product.id,
                "asin": product.asin,
                "title": product.title,
                "period_days": days,
                "data_points": len(history),
                "history": history,
                "statistics": stats,
            }
    except Exception as e:
        return {"error": f"Failed to retrieve price history: {str(e)}"}


@mcp_server.tool()
async def get_bsr_history(product_id: UUID, days: int = 30) -> dict[str, Any]:
    """Get Best Seller Rank (BSR) history for a product.

    Args:
        product_id: The ID of the product
        days: Number of days of history to retrieve (default: 30)

    Returns:
        BSR history data with timestamps and rankings
    """
    from datetime import datetime, timedelta

    try:
        async with get_async_db_context() as db:
            # Get product
            product_result = await db.execute(select(Product).where(Product.id == product_id))
            product = product_result.scalar_one_or_none()

            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            cutoff_date = datetime.now() - timedelta(days=days)

            snapshots_result = await db.execute(
                select(ProductSnapshot)
                .where(
                    ProductSnapshot.product_id == product_id,
                    ProductSnapshot.scraped_at >= cutoff_date,
                )
                .order_by(ProductSnapshot.scraped_at)
            )
            snapshots = snapshots_result.scalars().all()

            history = [
                {
                    "timestamp": snap.scraped_at.isoformat(),
                    "bsr": snap.bsr_main_category,
                    "bsr_small": snap.bsr_small_category,
                    "main_category": snap.main_category_name,
                    "small_category": snap.small_category_name,
                }
                for snap in snapshots
            ]

            # Calculate statistics
            bsr_values: list[int] = [s["bsr"] for s in history if s["bsr"]]  # type: ignore[misc]
            stats: dict[str, int | float] = {}
            if bsr_values:
                stats = {
                    "best_rank": min(bsr_values),
                    "worst_rank": max(bsr_values),
                    "avg_rank": sum(bsr_values) / len(bsr_values),
                    "current_rank": bsr_values[-1],
                    "rank_change": bsr_values[-1] - bsr_values[0] if len(bsr_values) > 1 else 0,
                }

            return {
                "product_id": product.id,
                "asin": product.asin,
                "title": product.title,
                "category": product.category,
                "period_days": days,
                "data_points": len(history),
                "history": history,
                "statistics": stats,
            }
    except Exception as e:
        return {"error": f"Failed to retrieve BSR history: {str(e)}"}


@mcp_server.tool()
async def get_competitor_analysis(product_id: UUID) -> dict[str, Any]:
    """Get competitor analysis for a product.

    Finds competitors in the same category with is_competitor=True flag.

    Args:
        product_id: The ID of the product

    Returns:
        Competitor comparison data including pricing and rankings
    """
    try:
        async with get_async_db_context() as db:
            # Get product
            product_result = await db.execute(select(Product).where(Product.id == product_id))
            product = product_result.scalar_one_or_none()

            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            # Find competitors in same category/marketplace
            competitors_result = await db.execute(
                select(Product)
                .where(
                    Product.marketplace == product.marketplace,
                    Product.category == product.category,
                    Product.is_competitor,
                    Product.is_active,
                    Product.id != product_id,
                )
                .limit(10)
            )
            competitors = competitors_result.scalars().all()

            competitors_data = []
            for competitor in competitors:
                latest_snapshot_result = await db.execute(
                    select(ProductSnapshot)
                    .where(ProductSnapshot.product_id == competitor.id)
                    .order_by(ProductSnapshot.scraped_at.desc())
                    .limit(1)
                )
                latest_snapshot = latest_snapshot_result.scalar_one_or_none()

                competitors_data.append(
                    {
                        "id": competitor.id,
                        "asin": competitor.asin,
                        "title": competitor.title,
                        "brand": competitor.brand,
                        "current_price": float(latest_snapshot.price)
                        if latest_snapshot and latest_snapshot.price
                        else None,
                        "current_bsr": latest_snapshot.bsr_main_category
                        if latest_snapshot
                        else None,
                        "rating": competitor.rating,
                        "review_count": competitor.review_count,
                    }
                )

            # Get current product data
            product_snapshot_result = await db.execute(
                select(ProductSnapshot)
                .where(ProductSnapshot.product_id == product_id)
                .order_by(ProductSnapshot.scraped_at.desc())
                .limit(1)
            )
            product_snapshot = product_snapshot_result.scalar_one_or_none()

            return {
                "product": {
                    "id": product.id,
                    "asin": product.asin,
                    "title": product.title,
                    "current_price": float(product_snapshot.price)
                    if product_snapshot and product_snapshot.price
                    else None,
                    "current_bsr": product_snapshot.bsr_main_category if product_snapshot else None,
                    "rating": product.rating,
                    "review_count": product.review_count,
                },
                "competitors": competitors_data,
                "total_competitors": len(competitors_data),
            }
    except Exception as e:
        return {"error": f"Failed to analyze competitors: {str(e)}"}


@mcp_server.tool()
async def trigger_product_refresh(product_id: UUID) -> dict[str, Any]:
    """Trigger a manual refresh/scrape of product data.

    Args:
        product_id: The ID of the product to refresh

    Returns:
        Status of the refresh operation
    """
    from products.tasks import update_single_product

    try:
        async with get_async_db_context() as db:
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar_one_or_none()

            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            # Queue the scraping task
            update_single_product.send(product_id)

            return {
                "success": True,
                "product_id": product.id,
                "asin": product.asin,
                "message": "Product refresh queued successfully",
            }
    except Exception as e:
        return {"error": f"Failed to trigger refresh: {str(e)}"}


@mcp_server.tool()
async def get_user_products(user_id: UUID, limit: int = 20) -> list[dict[str, Any]]:
    """Get all products tracked by a specific user.

    Args:
        user_id: The ID of the user
        limit: Maximum number of products to return (default: 20)

    Returns:
        List of products tracked by the user
    """
    from users.models import User

    try:
        async with get_async_db_context() as db:
            # Verify user exists
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return []

            # Get products via join with UserProduct
            products_result = await db.execute(
                select(Product).join(UserProduct).where(UserProduct.user_id == user_id).limit(limit)
            )
            products = products_result.scalars().all()

            products_data = []
            for product in products:
                # Get latest snapshot
                snapshot_result = await db.execute(
                    select(ProductSnapshot)
                    .where(ProductSnapshot.product_id == product.id)
                    .order_by(ProductSnapshot.scraped_at.desc())
                    .limit(1)
                )
                latest_snapshot = snapshot_result.scalar_one_or_none()

                products_data.append(
                    {
                        "id": product.id,
                        "asin": product.asin,
                        "title": product.title,
                        "marketplace": product.marketplace,
                        "category": product.category,
                        "current_price": latest_snapshot.price if latest_snapshot else None,
                        "current_bsr": latest_snapshot.bsr_main_category
                        if latest_snapshot
                        else None,
                        "rating": product.rating,
                        "review_count": product.review_count,
                        "is_active": product.is_active,
                    }
                )

            return products_data
    except Exception:
        return []


@mcp_server.tool()
async def update_product_info(
    product_id: UUID,
    title: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    is_active: bool | None = None,
    price_change_threshold: float | None = None,
    bsr_change_threshold: float | None = None,
) -> dict[str, Any]:
    """Update basic product information and tracking settings.

    Args:
        product_id: The ID of the product to update
        title: New product title (optional)
        brand: New brand name (optional)
        category: New category (optional)
        is_active: Whether product tracking is active (optional)
        price_change_threshold: Alert threshold for price changes (optional)
        bsr_change_threshold: Alert threshold for BSR changes (optional)

    Returns:
        Updated product information
    """
    try:
        async with get_async_db_context() as db:
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar_one_or_none()

            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            # Update fields if provided
            if title is not None:
                product.title = title
            if brand is not None:
                product.brand = brand
            if category is not None:
                product.category = category
            if is_active is not None:
                product.is_active = is_active
            if price_change_threshold is not None:
                product.price_change_threshold = price_change_threshold
            if bsr_change_threshold is not None:
                product.bsr_change_threshold = bsr_change_threshold

            await db.commit()
            await db.refresh(product)

            return {
                "success": True,
                "product_id": product.id,
                "asin": product.asin,
                "title": product.title,
                "brand": product.brand,
                "category": product.category,
                "is_active": product.is_active,
                "price_change_threshold": product.price_change_threshold,
                "bsr_change_threshold": product.bsr_change_threshold,
                "message": "Product updated successfully",
            }
    except Exception as e:
        return {"error": f"Failed to update product: {str(e)}"}


@mcp_server.tool()
async def update_user_product_settings(
    user_id: UUID,
    product_id: UUID,
    is_primary: bool | None = None,
    price_change_threshold: float | None = None,
    bsr_change_threshold: float | None = None,
    notes: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Update user-specific product settings (through UserProduct relationship).

    Args:
        user_id: The ID of the user
        product_id: The ID of the product
        is_primary: Whether this is user's primary product (optional)
        price_change_threshold: Custom price alert threshold (optional)
        bsr_change_threshold: Custom BSR alert threshold (optional)
        notes: User notes about this product (optional)
        tags: List of tags for organization (optional)

    Returns:
        Updated user-product settings
    """
    try:
        async with get_async_db_context() as db:
            # Get the UserProduct relationship
            result = await db.execute(
                select(UserProduct).where(
                    UserProduct.user_id == user_id,
                    UserProduct.product_id == product_id,
                )
            )
            user_product = result.scalar_one_or_none()

            if not user_product:
                return {"error": f"User {user_id} does not own product {product_id}"}

            # Update fields if provided
            if is_primary is not None:
                user_product.is_primary = is_primary
            if price_change_threshold is not None:
                user_product.price_change_threshold = price_change_threshold
            if bsr_change_threshold is not None:
                user_product.bsr_change_threshold = bsr_change_threshold
            if notes is not None:
                user_product.notes = notes
            if tags is not None:
                user_product.tags = tags

            await db.commit()
            await db.refresh(user_product)

            return {
                "success": True,
                "user_id": user_id,
                "product_id": product_id,
                "is_primary": user_product.is_primary,
                "price_change_threshold": user_product.price_change_threshold,
                "bsr_change_threshold": user_product.bsr_change_threshold,
                "notes": user_product.notes,
                "tags": user_product.tags,
                "message": "User product settings updated successfully",
            }
    except Exception as e:
        return {"error": f"Failed to update settings: {str(e)}"}


@mcp_server.tool()
async def toggle_product_tracking(product_id: UUID, is_active: bool) -> dict[str, Any]:
    """Enable or disable tracking for a product.

    Args:
        product_id: The ID of the product
        is_active: True to enable tracking, False to disable

    Returns:
        Updated product status
    """
    try:
        async with get_async_db_context() as db:
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar_one_or_none()

            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            product.is_active = is_active
            await db.commit()
            await db.refresh(product)

            return {
                "success": True,
                "product_id": product.id,
                "asin": product.asin,
                "title": product.title,
                "is_active": product.is_active,
                "message": f"Product tracking {'enabled' if is_active else 'disabled'}",
            }
    except Exception as e:
        return {"error": f"Failed to toggle tracking: {str(e)}"}


@mcp_server.tool()
async def update_alert_thresholds(
    product_id: UUID,
    price_threshold: float | None = None,
    bsr_threshold: float | None = None,
) -> dict[str, Any]:
    """Update alert thresholds for a product.

    Args:
        product_id: The ID of the product
        price_threshold: Price change alert threshold percentage (optional)
        bsr_threshold: BSR change alert threshold percentage (optional)

    Returns:
        Updated threshold settings
    """
    try:
        async with get_async_db_context() as db:
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar_one_or_none()

            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            if price_threshold is not None:
                product.price_change_threshold = price_threshold
            if bsr_threshold is not None:
                product.bsr_change_threshold = bsr_threshold

            await db.commit()
            await db.refresh(product)

            return {
                "success": True,
                "product_id": product.id,
                "asin": product.asin,
                "title": product.title,
                "price_change_threshold": product.price_change_threshold,
                "bsr_change_threshold": product.bsr_change_threshold,
                "message": "Alert thresholds updated successfully",
            }
    except Exception as e:
        return {"error": f"Failed to update thresholds: {str(e)}"}


# ============================================================================
# AI SUGGESTION TOOLS
# ============================================================================


@mcp_server.tool()
async def create_suggestion(
    title: str,
    description: str,
    reasoning: str,
    product_id: UUID | None = None,
    priority: str = "medium",
    category: str = "general",
    confidence_score: float | None = None,
    estimated_impact: dict[str, Any] | None = None,
    expires_in_days: int | None = None,
) -> dict[str, Any]:
    """Create a new AI-generated suggestion.

    Args:
        title: Brief title/summary of the suggestion
        description: Detailed description
        reasoning: AI reasoning and analysis
        product_id: Product ID this suggestion applies to (optional)
        priority: Priority level (low, medium, high, critical)
        category: Category (pricing, content, tracking, competition, etc.)
        confidence_score: AI confidence (0-1)
        estimated_impact: Dict of estimated impact metrics
        expires_in_days: Days until suggestion expires

    Returns:
        Created suggestion with ID
    """
    from datetime import datetime, timedelta

    try:
        # Calculate expiration date if provided
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create suggestion
        async with get_async_db_context() as db:
            suggestion = Suggestion(
                title=title,
                description=description,
                reasoning=reasoning,
                product_id=product_id,
                priority=priority,
                category=category,
                confidence_score=confidence_score,
                estimated_impact=estimated_impact or {},
                expires_at=expires_at,
            )
            db.add(suggestion)
            await db.commit()
            await db.refresh(suggestion)

            return {
                "success": True,
                "suggestion_id": suggestion.id,
                "title": suggestion.title,
                "status": suggestion.status,
                "message": "Suggestion created successfully. Now add actions to it.",
            }
    except Exception as e:
        return {"error": f"Failed to create suggestion: {str(e)}"}


@mcp_server.tool()
async def add_suggestion_action(
    suggestion_id: UUID,
    action_type: str,
    target_field: str,
    proposed_value: str,
    current_value: str | None = None,
    reasoning: str = "",
    impact_description: str | None = None,
    order: int = 0,
) -> dict[str, Any]:
    """Add an action to an existing suggestion.

    Args:
        suggestion_id: ID of the suggestion
        action_type: Type of action (update_price, update_title, update_description,
                    update_brand, adjust_price_threshold, adjust_bsr_threshold, toggle_tracking)
        target_field: Field to modify (price, title, description, etc.)
        proposed_value: New value to set
        current_value: Current value for reference
        reasoning: Specific reasoning for this action
        impact_description: Expected impact description
        order: Order of action within suggestion

    Returns:
        Created action details
    """
    try:
        async with get_async_db_context() as db:
            # Verify suggestion exists
            suggestion_result = await db.execute(
                select(Suggestion).where(Suggestion.id == suggestion_id)
            )
            suggestion = suggestion_result.scalar_one_or_none()
            if not suggestion:
                return {"error": f"Suggestion with ID {suggestion_id} not found"}

            # Create action
            action = SuggestionAction(
                suggestion_id=suggestion.id,
                action_type=action_type,
                target_field=target_field,
                current_value=current_value,
                proposed_value=proposed_value,
                reasoning=reasoning or f"Amazcope suggests updating {target_field}",
                impact_description=impact_description,
                order=order,
            )
            db.add(action)
            await db.commit()
            await db.refresh(action)

            return {
                "success": True,
                "action_id": action.id,
                "suggestion_id": suggestion.id,
                "action_type": action.action_type,
                "target_field": action.target_field,
                "message": "Action added to suggestion",
            }
    except Exception as e:
        return {"error": f"Failed to add action: {str(e)}"}


@mcp_server.tool()
async def propose_price_optimization(
    product_id: UUID,
    suggested_price: float,
    reasoning: str,
    estimated_revenue_impact: str | None = None,
) -> dict[str, Any]:
    """Propose a price optimization for a product.

    This is a convenience tool that creates a suggestion with a price change action.

    Args:
        product_id: Product ID
        suggested_price: Suggested new price
        reasoning: Why this price is recommended
        estimated_revenue_impact: Estimated revenue impact (e.g., "+15%")

    Returns:
        Created suggestion and action IDs
    """
    async with get_async_db_context() as db:
        # Get product
        product_result = await db.execute(select(Product).where(Product.id == product_id))
        product = product_result.scalar_one_or_none()
        if not product:
            return {"error": f"Product with ID {product_id} not found"}

        # Get current price from latest snapshot
        snapshot_result = await db.execute(
            select(ProductSnapshot)
            .where(ProductSnapshot.product_id == product_id)
            .order_by(ProductSnapshot.scraped_at.desc())
            .limit(1)
        )
        latest_snapshot = snapshot_result.scalar_one_or_none()
        current_price = (
            float(latest_snapshot.price) if latest_snapshot and latest_snapshot.price else None
        )

        # Create suggestion
        estimated_impact = {}
        if estimated_revenue_impact:
            estimated_impact["revenue_change"] = estimated_revenue_impact

        suggestion = Suggestion(
            title=f"Price Optimization for {product.title[:50]}",
            description=f"Adjust price to ${suggested_price} for optimal revenue/conversion balance",
            reasoning=reasoning,
            product_id=product.id,
            priority=SuggestionPriority.HIGH
            if current_price and abs(suggested_price - current_price) / current_price > 0.10
            else SuggestionPriority.MEDIUM,
            category=SuggestionCategory.PRICING,
            estimated_impact=estimated_impact,
        )
        db.add(suggestion)
        await db.flush()

        # Add action
        action = SuggestionAction(
            suggestion_id=suggestion.id,
            action_type=ActionType.UPDATE_PRICE,
            target_field="price",
            current_value=str(current_price) if current_price else "Unknown",
            proposed_value=str(suggested_price),
            reasoning=reasoning,
            impact_description=estimated_revenue_impact,
        )
        db.add(action)
        await db.commit()
        await db.refresh(suggestion)
        await db.refresh(action)

        return {
            "success": True,
            "suggestion_id": suggestion.id,
            "action_id": action.id,
            "product_asin": product.asin,
            "current_price": current_price,
            "suggested_price": suggested_price,
            "message": "Price optimization suggestion created",
        }


@mcp_server.tool()
async def propose_content_improvement(
    product_id: UUID,
    field_to_improve: str,
    current_content: str,
    improved_content: str,
    reasoning: str,
    expected_benefit: str | None = None,
) -> dict[str, Any]:
    """Propose content improvements for a product (title, description, etc.).

    Args:
        product_id: Product ID
        field_to_improve: Field name (title, description, brand, category)
        current_content: Current content
        improved_content: Improved version
        reasoning: Why this improvement is recommended
        expected_benefit: Expected benefit (e.g., "Better SEO", "Clearer value proposition")

    Returns:
        Created suggestion and action IDs
    """
    try:
        async with get_async_db_context() as db:
            # Get product
            product_result = await db.execute(select(Product).where(Product.id == product_id))
            product = product_result.scalar_one_or_none()
            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            # Create suggestion
            suggestion = Suggestion(
                title=f"Content Improvement: {field_to_improve.title()} for {product.title[:40]}",
                description=f"Improve {field_to_improve} to enhance product discoverability and conversion",
                reasoning=reasoning,
                product_id=product.id,
                priority=SuggestionPriority.MEDIUM,
                category=SuggestionCategory.CONTENT,
                estimated_impact={"benefit": expected_benefit} if expected_benefit else {},
            )
            db.add(suggestion)
            await db.flush()

            # Map field names to action type enums
            field_to_action_type = {
                "title": ActionType.UPDATE_TITLE,
                "description": ActionType.UPDATE_DESCRIPTION,
                "brand": ActionType.UPDATE_BRAND,
                "category": ActionType.UPDATE_CATEGORY,
            }

            action_type_enum = field_to_action_type.get(
                field_to_improve,
                ActionType.UPDATE_TITLE,  # fallback default
            )

            # Add action
            action = SuggestionAction(
                suggestion_id=suggestion.id,
                action_type=action_type_enum,
                target_field=field_to_improve,
                current_value=current_content,
                proposed_value=improved_content,
                reasoning=reasoning,
                impact_description=expected_benefit,
            )
            db.add(action)
            await db.commit()
            await db.refresh(suggestion)
            await db.refresh(action)

            return {
                "success": True,
                "suggestion_id": suggestion.id,
                "action_id": action.id,
                "field": field_to_improve,
                "message": f"{field_to_improve.title()} improvement suggestion created",
            }
    except Exception as e:
        return {"error": f"Failed to create content suggestion: {str(e)}"}


@mcp_server.tool()
async def propose_tracking_adjustment(
    product_id: UUID,
    adjustment_type: str,
    new_value: str,
    reasoning: str,
) -> dict[str, Any]:
    """Propose tracking setting adjustments (thresholds, active status, frequency).

    Args:
        product_id: Product ID
        adjustment_type: Type of adjustment (price_threshold, bsr_threshold, toggle_tracking)
        new_value: New value to set
        reasoning: Why this adjustment is recommended

    Returns:
        Created suggestion and action IDs
    """
    try:
        async with get_async_db_context() as db:
            # Get product
            product_result = await db.execute(select(Product).where(Product.id == product_id))
            product = product_result.scalar_one_or_none()
            if not product:
                return {"error": f"Product with ID {product_id} not found"}

            # Determine action details
            action_type_map = {
                "price_threshold": (
                    ActionType.ADJUST_PRICE_THRESHOLD,
                    "price_change_threshold",
                ),
                "bsr_threshold": (
                    ActionType.ADJUST_BSR_THRESHOLD,
                    "bsr_change_threshold",
                ),
                "toggle_tracking": (ActionType.TOGGLE_TRACKING, "is_active"),
            }

            if adjustment_type not in action_type_map:
                return {"error": f"Unknown adjustment type: {adjustment_type}"}

            action_type_enum, target_field = action_type_map[adjustment_type]

            # Get current value
            current_value = str(getattr(product, target_field, "Unknown"))

            # Create suggestion
            suggestion = Suggestion(
                title=f"Tracking Adjustment for {product.title[:40]}",
                description=f"Adjust {target_field} to optimize tracking efficiency",
                reasoning=reasoning,
                product_id=product.id,
                priority=SuggestionPriority.LOW,
                category=SuggestionCategory.TRACKING,
            )
            db.add(suggestion)
            await db.flush()

            # Add action
            action = SuggestionAction(
                suggestion_id=suggestion.id,
                action_type=action_type_enum,
                target_field=target_field,
                current_value=current_value,
                proposed_value=new_value,
                reasoning=reasoning,
            )
            db.add(action)
            await db.commit()
            await db.refresh(suggestion)
            await db.refresh(action)

            return {
                "success": True,
                "suggestion_id": suggestion.id,
                "action_id": action.id,
                "adjustment": adjustment_type,
                "message": "Tracking adjustment suggestion created",
            }
    except Exception as e:
        return {"error": f"Failed to create tracking suggestion: {str(e)}"}


@mcp_server.tool()
async def get_pending_suggestions(
    product_id: UUID | None = None, priority: str | None = None, limit: int = 20
) -> list[dict[str, Any]]:
    """Get list of pending suggestions awaiting user review.

    Args:
        product_id: Filter by product ID (optional)
        priority: Filter by priority (low, medium, high, critical)
        limit: Maximum number of suggestions to return

    Returns:
        List of pending suggestions with action counts
    """
    from datetime import datetime

    try:
        async with get_async_db_context() as db:
            # Build query
            query = select(Suggestion).where(
                Suggestion.status == SuggestionStatus.PENDING,
                Suggestion.expires_at > datetime.utcnow(),
            )

            if product_id:
                query = query.where(Suggestion.product_id == product_id)
            if priority:
                query = query.where(Suggestion.priority == priority)

            query = (
                query.order_by(Suggestion.created_at.desc())
                .limit(limit)
                .options(selectinload(Suggestion.actions))
            )

            result = await db.execute(query)
            suggestions = result.scalars().all()

            result_list = []
            for suggestion in suggestions:
                action_count = len(suggestion.actions) if suggestion.actions else 0
                pending_actions = (
                    sum(1 for a in suggestion.actions if a.status == ActionStatus.PENDING)
                    if suggestion.actions
                    else 0
                )

                # Get product data if available
                product_data = None
                if suggestion.product_id:
                    product_result = await db.execute(
                        select(Product).where(Product.id == suggestion.product_id)
                    )
                    product_data = product_result.scalar_one_or_none()

                result_list.append(
                    {
                        "id": suggestion.id,
                        "title": suggestion.title,
                        "description": suggestion.description,
                        "priority": suggestion.priority,
                        "category": suggestion.category,
                        "product_id": suggestion.product_id,
                        "product_title": product_data.title if product_data else None,
                        "confidence_score": suggestion.confidence_score,
                        "total_actions": action_count,
                        "pending_actions": pending_actions,
                        "created_at": suggestion.created_at.isoformat()
                        if suggestion.created_at
                        else None,
                    }
                )

            return result_list
    except Exception as e:
        return [{"error": f"Failed to fetch suggestions: {str(e)}"}]


@mcp_server.tool()
async def generate_daily_report(
    products_analyzed: int,
    suggestions_created: int,
    critical_issues: int,
    opportunities: int,
    summary_message: str,
    market_insights: str | None = None,
    action_items: list[str] | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Generate and send a comprehensive daily report via notification system.

    Creates a daily report summarizing AI analysis results, product performance,
    and optimization opportunities. Sends both in-app notifications and email
    reports to users based on their notification preferences.

    Args:
        products_analyzed: Number of products analyzed today
        suggestions_created: Number of AI suggestions generated
        critical_issues: Number of critical issues found
        opportunities: Number of optimization opportunities
        summary_message: AI-generated summary of the day's analysis
        market_insights: Optional market insights and trends
        action_items: Optional list of recommended actions
        user_id: Optional specific user ID (sends to all users if None)

    Returns:
        dict: Report delivery statistics with success/error counts
    """
    import uuid
    from datetime import datetime

    from notification.topics import daily_report_topic

    # Parse user_id if provided
    target_user_id = None
    if user_id:
        target_user_id = uuid.UUID(user_id)
    # Prepare report data
    report_data = {
        "products_analyzed": products_analyzed,
        "suggestions_created": suggestions_created,
        "critical_issues": critical_issues,
        "opportunities": opportunities,
        "summary_message": summary_message,
        "market_insights": market_insights,
        "action_items": action_items or [],
        "suggestions": [],  # This will be populated with recent suggestions
    }

    # Get recent suggestions for the report
    async with get_async_db_context() as db:
        from sqlalchemy.orm import selectinload

        # Get suggestions created today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        suggestions_query = (
            select(Suggestion)
            .where(Suggestion.created_at >= today_start)
            .options(selectinload(Suggestion.product))
            .order_by(Suggestion.priority.desc(), Suggestion.created_at.desc())
            .limit(10)  # Top 10 suggestions for email
        )

        result = await db.execute(suggestions_query)
        suggestions = result.scalars().all()

        # Format suggestions for template
        formatted_suggestions = []
        for suggestion in suggestions:
            product = suggestion.product if hasattr(suggestion, "product") else None

            suggestion_data: dict[str, Any] = {
                "title": suggestion.title,
                "description": suggestion.description,
                "priority": suggestion.priority,
                "product_title": product.title if product else "Unknown Product",
                "product_asin": product.asin if product else "N/A",
                "category": product.category if product else None,
                "metrics": [],  # Could be populated with specific metrics
            }

            # Add priority-based styling
            if (
                "critical" in suggestion.priority.lower()
                if isinstance(suggestion.priority, str)
                else False
            ):
                suggestion_data["priority"] = "critical"
            elif (
                "high" in suggestion.priority.lower()
                if isinstance(suggestion.priority, str)
                else False
            ):
                suggestion_data["priority"] = "high"
            elif (
                "medium" in suggestion.priority.lower()
                if isinstance(suggestion.priority, str)
                else False
            ):
                suggestion_data["priority"] = "medium"
            else:
                suggestion_data["priority"] = "low"

            formatted_suggestions.append(suggestion_data)

        report_data["suggestions"] = formatted_suggestions

    # Send report via notification topic
    result = await daily_report_topic.send(
        user_id=target_user_id,
        title=f"Daily Report - {datetime.utcnow().strftime('%B %d, %Y')}",
        message=f"Amazcope analyzed {products_analyzed} products and created {suggestions_created} optimization suggestions",
        priority="normal",
        action_url="/dashboard",
        email_subject=f"Your Daily Amazon Optimization Report - {datetime.utcnow().strftime('%B %d')}",
        **report_data,  # type: ignore[arg-type]
    )

    return {
        "success": True,
        "report_generated": True,
        "notifications_sent": result.get("notifications_created", 0),
        "emails_sent": result.get("emails_sent", 0),
        "errors": result.get("errors", []),
        "report_date": datetime.utcnow().isoformat(),
        "products_included": products_analyzed,
        "suggestions_included": len(formatted_suggestions),
    }
