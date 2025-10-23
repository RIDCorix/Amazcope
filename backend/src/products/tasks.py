"""Dramatiq actors for product tracking and monitoring."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db_context, get_sync_db
from core.dramatiq_app import dramatiq
from mcp_server.tools import (
    generate_daily_report,
    get_bsr_history,
    get_competitor_analysis,
    get_price_history,
    get_product_details,
    propose_content_improvement,
    propose_price_optimization,
    propose_tracking_adjustment,
)
from products.models import Category, Product, ProductSnapshot
from scrapper.product_tracking_service import ProductTrackingService
from services.apify_service import ApifyService
from users.models import User
from utils.ai_tools import (
    execute_ai_function_calls,
    generate_tool_spec,
    get_system_prompt,
)
from utils.db_helpers import (
    get_active_products,
    get_products_by_ids,
    get_recent_snapshots,
)

logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=3, min_backoff=300000, max_backoff=900000)
def daily_product_update() -> None:
    """Update all active products daily.

    This task:
    1. Fetches all active products
    2. Scrapes latest data from Amazon
    3. Creates new snapshots
    4. Checks for threshold violations
    5. Generates alerts if needed

    Runs daily at 2 AM (configured in APScheduler).
    """

    async def _update_all_products() -> None:
        try:
            # Get all active products using helper function
            products = await get_active_products()
            product_ids = [p.id for p in products]

            logger.info(f"Starting daily update for {len(product_ids)} products")

            # Batch update all products
            async with get_async_db_context() as db:
                service = ProductTrackingService(db)
                result = await service.batch_update_products(product_ids)

            logger.info(
                f"Daily update completed. Success: {result['success']}, Failed: {result['failed']}"
            )

        except Exception as exc:
            logger.error(f"Daily product update failed: {str(exc)}")
            raise  # Dramatiq will handle retries via middleware

    # Run the async function
    asyncio.run(_update_all_products())


@dramatiq.actor(max_retries=3, min_backoff=60000, max_backoff=300000)
def update_single_product(product_id: int) -> None:
    """Update a single product (manual trigger or quick refresh).

    Args:
        product_id: ID of the product to update
    """

    async def _update_product() -> None:
        try:
            # Get the product using helper function
            products = await get_products_by_ids([product_id])
            if not products:
                logger.error(f"Product {product_id} not found")
                return

            product = products[0]
            logger.info(f"Updating product {product_id} (ASIN: {product.asin})")

            # Update the product
            async with get_async_db_context() as db:
                service = ProductTrackingService(db)
                snapshot = await service.update_product(product_id, check_alerts=True)  # type: ignore[arg-type]

            logger.info(f"Product {product_id} updated successfully (snapshot_id: {snapshot.id})")

        except Exception as exc:
            logger.error(f"Failed to update product {product_id}: {str(exc)}")
            raise  # Dramatiq will handle retries via middleware

    asyncio.run(_update_product())


@dramatiq.actor
def cleanup_old_snapshots(days: int = 90) -> None:
    """Delete snapshots older than specified days.

    Args:
        days: Number of days to retain (default 90)
    """

    async def _cleanup() -> None:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            async with get_async_db_context() as db:
                # Delete old snapshots
                stmt = delete(ProductSnapshot).where(ProductSnapshot.scraped_at < cutoff_date)
                result = await db.execute(stmt)
                await db.commit()
                deleted_count = result.rowcount

            logger.info(
                f"Cleaned up {deleted_count} snapshots older than {days} days (cutoff: {cutoff_date.isoformat()})"
            )

        except Exception as e:
            logger.error(f"Failed to cleanup snapshots: {str(e)}")

    asyncio.run(_cleanup())


@dramatiq.actor(max_retries=3, min_backoff=120000, max_backoff=600000)
async def scrape_category_bestsellers(category_url: str, max_items: int = 50) -> None:
    """Scrape top bestseller products from a category and create products.

    This task:
    1. Scrapes bestsellers using Apify with Pydantic validation
    2. Creates Product records for all products (new and existing)
    3. Creates CategoryMetric with aggregated statistics

    Args:
        category_url: Amazon category/bestsellers URL
        max_items: Maximum number of products to scrape (default 50)
    """

    apify = ApifyService()

    # Get or create Category record
    async with get_async_db_context() as db:
        category = await _get_or_create_category(db, category_url)

    logger.info(f"Scraping bestsellers for category: {category.name}")

    # Scrape bestsellers with Pydantic validation
    bestsellers_data = await apify.scrape_bestsellers(
        category_url=category_url, max_items=max_items
    )

    if not bestsellers_data:
        logger.warning(f"No bestsellers data returned for category: {category.name}")
        return

    logger.info(f"Found {len(bestsellers_data)} bestsellers in category {category.name}")

    # Process bestsellers and create products
    async with get_async_db_context() as db:
        products = await _create_products_from_bestsellers(db, bestsellers_data, category, apify)

        # Create CategoryMetric from the scraped products
        await _create_category_metric(db, category, products)

    logger.info(
        f"Bestsellers scraping completed for {category.name}: {len(products)} products processed"
    )


async def _get_or_create_category(db: AsyncSession, category_url: str) -> Category:
    """Get or create Category record."""
    # Extract category name from URL
    category_name = category_url.split("/")[-1] or "Unknown Category"

    result = await db.execute(select(Category).where(Category.url == category_url))
    category = result.scalar_one_or_none()

    if not category:
        category = Category(url=category_url, name=category_name)
        category.category_id = category.parse_category_id()
        db.add(category)
        await db.commit()
        await db.refresh(category)

    return category


async def _create_products_from_bestsellers(
    db: Any, bestsellers_data: list[dict[str, Any]], category: Category, apify: ApifyService
) -> list[Product]:
    """Create Product records from bestseller data."""
    from schemas.apify_schemas import BestsellerItem

    products = []

    for item_data in bestsellers_data:
        # Validate with Pydantic
        item = BestsellerItem(**item_data)

        # Extract ASIN from URL
        asin = _extract_asin_from_url(item.url)
        if not asin:
            logger.warning(f"Could not extract ASIN from URL: {item.url}")
            continue

        # Extract marketplace from URL
        marketplace = apify.extract_marketplace_from_url(item.url)

        # Check if product exists
        result = await db.execute(
            select(Product).where(
                Product.asin == asin,
                Product.marketplace == marketplace,
            )
        )
        existing_product = result.scalar_one_or_none()

        if existing_product:
            products.append(existing_product)
            logger.debug(f"Product {asin} already exists")
            continue

        # Create new product record
        product = Product(
            asin=asin,
            marketplace=marketplace,
            title=item.name,
            url=item.url,
            image_url=item.thumbnail_url,
            category=category.name,
            is_competitor=True,
            is_active=False,
        )
        db.add(product)
        await db.flush()  # Get the product ID
        products.append(product)

        logger.info(f"Created competitor product: {asin} - {product.title[:50]}...")

    await db.commit()
    return products


def _extract_asin_from_url(url: str) -> str | None:
    """Extract ASIN from Amazon product URL."""
    import re

    # Pattern: /dp/ASIN or /gp/product/ASIN
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
    if match:
        return match.group(1)
    return None


async def _create_category_metric(db: Any, category: Category, products: list[Product]) -> None:
    """Create CategoryMetric with aggregated statistics from products."""
    from decimal import Decimal
    from statistics import mean, median

    from products.models import CategoryMetric

    if not products:
        logger.warning(f"No products to create metrics for category {category.name}")
        return

    # Get latest snapshots for all products
    product_ids = [p.id for p in products]
    result = await db.execute(
        select(ProductSnapshot)
        .where(ProductSnapshot.product_id.in_(product_ids))
        .order_by(ProductSnapshot.product_id, ProductSnapshot.scraped_at.desc())
    )
    all_snapshots = result.scalars().all()

    # Get latest snapshot per product
    latest_snapshots = {}
    for snapshot in all_snapshots:
        if snapshot.product_id not in latest_snapshots:
            latest_snapshots[snapshot.product_id] = snapshot

    snapshots_list = list(latest_snapshots.values())

    if not snapshots_list:
        logger.warning(f"No snapshots found for products in category {category.name}")
        return

    # Calculate metrics
    prices = [float(s.price) for s in snapshots_list if s.price]
    bsrs = [s.bsr_main_category for s in snapshots_list if s.bsr_main_category]
    ratings = [s.rating for s in snapshots_list if s.rating]
    review_counts = [s.review_count for s in snapshots_list if s.review_count]

    metric = CategoryMetric(
        category_id=category.id,
        category_level="main",
        recorded_at=datetime.utcnow(),
        avg_price=Decimal(str(mean(prices))) if prices else None,
        median_price=Decimal(str(median(prices))) if prices else None,
        min_price=Decimal(str(min(prices))) if prices else None,
        max_price=Decimal(str(max(prices))) if prices else None,
        avg_bsr=int(mean(bsrs)) if bsrs else None,
        median_bsr=int(median(bsrs)) if bsrs else None,
        avg_rating=mean(ratings) if ratings else None,
        avg_review_count=int(mean(review_counts)) if review_counts else None,
        product_count=len(products),
    )

    db.add(metric)
    await db.commit()

    logger.info(
        f"Created CategoryMetric for {category.name}: "
        f"{len(products)} products, avg_price={metric.avg_price}, avg_rating={metric.avg_rating}"
    )


@dramatiq.actor(max_retries=2, min_backoff=600000, max_backoff=1800000)
def daily_ai_suggestions() -> None:
    """Generate AI-powered optimization suggestions for all users daily.

    This is the main entry point that:
    1. Gets all users who have active products
    2. Spawns per-user AI suggestion subtasks
    3. Tracks overall progress
    """
    # Use SYNC database session for Dragatiq tasks (no asyncio.run needed!)
    db = get_sync_db()
    try:
        # Get all users who have active products using sync query
        query = select(User).join(Product).where(Product.is_active).distinct()
        result = db.execute(query)
        users = result.scalars().all()

        if not users:
            logger.info("No users with active products found for AI suggestions")
            return

        logger.info(f"Starting AI suggestions for {len(users)} users")

        # Spawn per-user AI suggestion tasks
        tasks_spawned = 0
        for user in users:
            # Get user's product count using sync query
            product_count_query = select(Product.id).where(
                Product.created_by_id == user.id, Product.is_active
            )
            product_result = db.execute(product_count_query)
            product_count = len(product_result.scalars().all())

            if product_count > 0:
                # Spawn async subtask for this user (includes personalized report generation)
                generate_user_ai_suggestions.send(str(user.id))
                tasks_spawned += 1
                logger.info(
                    f"Spawned AI suggestions task for user {user.id} ({product_count} products)"
                )

        logger.info(
            f"Daily AI suggestions orchestration completed: "
            f"{tasks_spawned} user tasks spawned for {len(users)} users"
        )

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Error in daily_ai_suggestions: {e}")
        raise
    finally:
        db.close()


@dramatiq.actor(max_retries=2, min_backoff=300000, max_backoff=900000)
async def generate_user_ai_suggestions(user_id: int) -> None:
    """Generate AI-powered optimization suggestions for a single user's products.

    Args:
        user_id: ID of the user to process
    """

    # Get user's active products updated in last 7 days
    products = await get_active_products(limit=50, updated_since_days=7, user_id=user_id)

    if not products:
        logger.info(f"No active products found for user {user_id}")
        return

    logger.info(f"Starting AI analysis for user {user_id} with {len(products)} products")

    # Setup AI tools and client
    tool_functions = [
        get_product_details,
        get_price_history,
        get_bsr_history,
        get_competitor_analysis,
        propose_price_optimization,
        propose_content_improvement,
        propose_tracking_adjustment,
        generate_daily_report,
    ]

    tools = [generate_tool_spec(func.fn) for func in tool_functions]
    system_prompt = get_system_prompt()

    suggestions_created = 0
    products_analyzed = 0

    # Process each product with AI
    for product in products:
        try:
            # Get recent snapshots for context
            recent_snapshots = await get_recent_snapshots(product.id, limit=10, days_back=7)

            if not recent_snapshots:
                logger.debug(f"No recent snapshots for product {product.id}, skipping")
                continue

            latest = recent_snapshots[0]

            # Create AI conversation for this product
            user_message = await _build_product_analysis_message(product, latest)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]

            # Execute AI function calls
            _, stats = await execute_ai_function_calls(
                messages=messages,
                tools=tools,
                tool_functions=tool_functions,
                max_iterations=10,
                model="gpt-4-turbo-preview",
            )

            suggestions_created += stats.get("suggestions_created", 0)
            products_analyzed += 1

            logger.info(
                f"Completed AI analysis for user {user_id} product {product.id} ({product.asin})"
            )

        except Exception as e:
            logger.error(
                f"Failed to analyze product {product.id} for user {user_id}: {str(e)}",
                exc_info=True,
            )
            continue

    # Generate personalized daily report for this user
    report_generated = False
    logger.info(f"Generating personalized daily report for user {user_id}...")

    # Get user's language preference for report generation
    user_language = "en"  # default
    try:
        from sqlalchemy.orm import selectinload

        from core.database import get_async_db_context

        async with get_async_db_context() as db_session:
            user_result = await db_session.execute(
                select(User).options(selectinload(User.settings)).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user and user.settings:
                user_language = user.settings.language or "en"
                logger.info(f"User {user_id} language preference: {user_language}")
    except Exception as lang_exc:
        logger.warning(f"Failed to get user language for {user_id}, using English: {str(lang_exc)}")

    # Map language codes to full names for clearer AI instruction
    language_names = {
        "en": "English",
        "zh": "Chinese (Traditional/Simplified)",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "ja": "Japanese",
        "ko": "Korean",
    }
    language_instruction = language_names.get(user_language, "English")

    # Setup AI tools for report generation (reuse tool_functions)
    report_message = f"""You MUST call the generate_daily_report function to create a comprehensive daily report for User {user_id}.

**IMPORTANT: Language Requirement**
⚠️ Generate ALL report content in {language_instruction} (user's preferred language: {user_language})
This includes: summary_message, market_insights, and action_items.

**Analysis Summary:**
- Analysis Date: {datetime.utcnow().strftime("%B %d, %Y")}
- User ID: {user_id}
- Products Analyzed: {products_analyzed}
- Suggestions Created: {suggestions_created}
- User Language: {user_language} ({language_instruction})

**Required Action:**
Immediately call the generate_daily_report function with the following parameters:
- products_analyzed: {products_analyzed}
- suggestions_created: {suggestions_created}
- critical_issues: (estimate based on analysis, default to 0 if unknown)
- opportunities: (estimate based on analysis, default to {suggestions_created})
- summary_message: A 2-3 sentence summary of today's key findings **in {language_instruction}**
- market_insights: Notable market trends or patterns observed **in {language_instruction}**
- action_items: List of 3-5 recommended actions for the seller **in {language_instruction}**
- user_id: "{user_id}"

**Guidelines:**
1. Provide data-driven insights based on the {products_analyzed} products analyzed
2. Categorize issues by priority (critical/high/medium/low)
3. Include specific, actionable recommendations
4. Highlight opportunities for optimization
5. Keep the tone professional and helpful
6. ⚠️ Write EVERYTHING in {language_instruction} - this is critical for user experience

Call the function NOW with realistic values based on the analysis performed."""

    report_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": report_message},
    ]

    # Execute AI report generation
    _, report_stats = await execute_ai_function_calls(
        messages=report_messages,
        tools=tools,
        tool_functions=tool_functions,
        max_iterations=5,
        model="gpt-4-turbo-preview",
        temperature=0.8,
    )

    # Check if report was actually generated
    reports_created = report_stats.get("reports_generated", 0)
    if reports_created > 0:
        report_generated = True
        logger.info(
            f"Personalized daily report generated for user {user_id} "
            f"(reports_created: {reports_created})"
        )
    else:
        logger.warning(
            f"Amazcope did not generate report for user {user_id}. Stats: {report_stats}"
        )

    logger.info(
        f"User {user_id} AI suggestions completed: "
        f"{products_analyzed} products analyzed, "
        f"{suggestions_created} suggestions created, "
        f"report generated: {report_generated}"
    )


async def _build_product_analysis_message(
    product: Product, latest_snapshot: ProductSnapshot
) -> str:
    """Build the AI analysis message for a product."""
    return f"""Analyze this Amazon product and provide optimization suggestions:

**Product Information:**
- ID: {product.id}
- ASIN: {product.asin}
- Title: {product.title}
- Marketplace: {product.marketplace}
- Category: {product.category}

**Current Metrics:**
- Price: ${latest_snapshot.price} {latest_snapshot.currency}
- BSR: #{latest_snapshot.bsr_main_category or "N/A"}
- Rating: {product.rating or "N/A"} ⭐
- Reviews: {product.review_count or 0}

**Instructions:**
1. First call get_price_history, get_bsr_history, and get_competitor_analysis to gather data
2. Analyze the trends and competitive position
3. Create 1-3 specific, actionable suggestions using the propose_* tools
4. Focus on data-driven recommendations with clear reasoning"""
