"""MCP Resources for data access.

Provides structured data resources that AI agents can read to understand
the current state of products, metrics, alerts, and reports.
"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database import get_async_db_context
from mcp_server.server import mcp_server
from products.models import Product, ProductSnapshot


@mcp_server.resource("product://list")
async def get_product_list() -> str:
    """Get a list of all active products in the system.

    Returns:
        Formatted list of products with basic information
    """
    async with get_async_db_context() as db:
        result = await db.execute(select(Product).where(Product.is_active).limit(100))
        products = result.scalars().all()

        output = ["# Active Products\n"]
        for product in products:
            output.append(
                f"- **{product.title}** (ASIN: {product.asin})\n"
                f"  - ID: {product.id}\n"
                f"  - Marketplace: {product.marketplace}\n"
                f"  - Category: {product.category}\n"
                f"  - Rating: {product.rating} ⭐ ({product.review_count} reviews)\n"
            )

        return "\n".join(output)


@mcp_server.resource("product://{product_id}")
async def get_product_resource(product_id: int) -> str:
    """Get detailed information about a specific product.

    Args:
        product_id: The ID of the product

    Returns:
        Formatted product details
    """
    try:
        async with get_async_db_context() as db:
            # Get product with relationships
            result = await db.execute(
                select(Product)
                .where(Product.id == product_id)
                .options(
                    selectinload(Product.user_products),
                    selectinload(Product.competitors),
                )
            )
            product = result.scalar_one_or_none()

            if not product:
                return f"Error loading product {product_id}: Product not found"

            # Get latest snapshot
            snapshot_result = await db.execute(
                select(ProductSnapshot)
                .where(ProductSnapshot.product_id == product_id)
                .order_by(ProductSnapshot.scraped_at.desc())
                .limit(1)
            )
            latest_snapshot = snapshot_result.scalar_one_or_none()

            output = [
                f"# {product.title}\n",
                f"**ASIN:** {product.asin}",
                f"**Marketplace:** {product.marketplace}",
                f"**Category:** {product.category}",
                f"**Brand:** {product.brand or 'N/A'}",
                "",
                "## Current Metrics",
            ]

            if latest_snapshot:
                if latest_snapshot.price:
                    output.extend(
                        [
                            f"- **Price:** {latest_snapshot.currency} {latest_snapshot.price}",
                            f"- **In Stock:** {'Yes' if latest_snapshot.in_stock else 'No'}",
                        ]
                    )
                if latest_snapshot.bsr_main_category:
                    output.extend(
                        [
                            f"- **Best Seller Rank:** #{latest_snapshot.bsr_main_category}",
                            f"- **Category:** {latest_snapshot.main_category_name or 'N/A'}",
                        ]
                    )

            output.extend(
                [
                    f"- **Rating:** {product.rating} ⭐",
                    f"- **Review Count:** {product.review_count}",
                    "",
                    "## Description",
                    product.product_description or "No description available",
                    "",
                    f"**Product URL:** {product.url}",
                    f"**Created:** {product.created_at.strftime('%Y-%m-%d')}",
                    f"**Last Updated:** {product.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                ]
            )

            if product.competitors:
                output.extend(
                    [
                        "",
                        "## Competitors",
                        f"Tracking {len(product.competitors)} competitor products",
                    ]
                )

            return "\n".join(output)

    except Exception as e:
        return f"Error loading product {product_id}: {str(e)}"


@mcp_server.resource("metrics://summary")
async def get_metrics_summary() -> str:
    """Get overall system metrics summary.

    Returns:
        Formatted metrics summary
    """
    from sqlalchemy import distinct, func

    async with get_async_db_context() as db:
        # Count total and active products
        total_result = await db.execute(select(func.count(Product.id)))
        total_products = total_result.scalar()

        active_result = await db.execute(select(func.count(Product.id)).where(Product.is_active))
        active_products = active_result.scalar()

        # Count snapshots
        snapshot_result = await db.execute(select(func.count(ProductSnapshot.id)))
        total_snapshots = snapshot_result.scalar()

        # Get distinct marketplaces
        marketplace_result = await db.execute(select(distinct(Product.marketplace)))
        marketplaces = [row[0] for row in marketplace_result.all()]

        # Count products by marketplace
        marketplace_counts = {}
        for marketplace in marketplaces:
            count_result = await db.execute(
                select(func.count(Product.id)).where(Product.marketplace == marketplace)
            )
            marketplace_counts[marketplace] = count_result.scalar()

        output = [
            "# System Metrics Summary\n",
            "## Product Statistics",
            f"- **Total Products:** {total_products}",
            f"- **Active Products:** {active_products}",
            f"- **Inactive Products:** {(total_products or 0) - (active_products or 0)}",
            "",
            "## Data Collection",
            f"- **Product Snapshots:** {total_snapshots}",
            "",
            "## Marketplaces",
        ]

        for marketplace, count in marketplace_counts.items():
            output.append(f"- **{marketplace}:** {count} products")

        return "\n".join(output)


@mcp_server.resource("alerts://active")
async def get_active_alerts() -> str:
    """Get all active alerts in the system.

    Returns:
        Formatted list of active alerts
    """
    from alert.models import Alert

    async with get_async_db_context() as db:
        result = await db.execute(
            select(Alert).where(Alert.is_active).options(selectinload(Alert.product)).limit(50)
        )
        alerts = result.scalars().all()

        output = ["# Active Alerts\n"]

        if not alerts:
            output.append("No active alerts configured.")
            return "\n".join(output)

        for alert in alerts:
            output.append(
                f"- **{alert.alert_type.upper()}** - {alert.product.title}\n"
                f"  - Threshold: {alert.threshold}\n"
                f"  - Condition: {alert.condition}\n"
                f"  - Status: {'🟢 Active' if alert.is_active else '🔴 Inactive'}\n"
            )

        return "\n".join(output)


@mcp_server.resource("optimization://suggestions/{product_id}")
async def get_optimization_suggestions(product_id: int) -> str:
    """Get AI-powered optimization suggestions for a product.

    Args:
        product_id: The ID of the product

    Returns:
        Formatted optimization suggestions
    """
    from optimization.models import Suggestion

    try:
        async with get_async_db_context() as db:
            # Get product
            product_result = await db.execute(select(Product).where(Product.id == product_id))
            product = product_result.scalar_one_or_none()

            if not product:
                return f"Error loading optimization suggestions for product {product_id}: Product not found"

            # Get suggestions
            suggestions_result = await db.execute(
                select(Suggestion)
                .where(Suggestion.product_id == product_id)
                .order_by(Suggestion.created_at.desc())
                .limit(10)
            )
            suggestions = suggestions_result.scalars().all()

            output = [
                f"# Optimization Suggestions for {product.title}\n",
                f"**ASIN:** {product.asin}",
                "",
            ]

            if not suggestions:
                output.append("No optimization suggestions available yet.")
                return "\n".join(output)

            for idx, suggestion in enumerate(suggestions, 1):
                output.extend(
                    [
                        f"## Suggestion {idx}: {suggestion.suggestion_type.replace('_', ' ').title()}",
                        f"**Priority:** {suggestion.priority or 'Normal'}",
                        f"**Status:** {suggestion.status}",
                        "",
                        str(suggestion.description),  # type: ignore[arg-type]
                        "",
                        f"*Generated: {suggestion.created_at.strftime('%Y-%m-%d %H:%M')}*",
                        "",
                        "---",
                        "",
                    ]
                )

            return "\n".join(output)

    except Exception as e:
        return f"Error loading optimization suggestions for product {product_id}: {str(e)}"


@mcp_server.resource("schema://product")
async def get_product_schema() -> str:
    """Get the product data schema definition.

    Returns:
        Product schema documentation
    """
    return """# Product Schema

## Fields

- **id** (integer): Unique product identifier
- **asin** (string): Amazon Standard Identification Number
- **title** (string): Product title/name
- **description** (text): Product description
- **marketplace** (string): Marketplace code (US, UK, DE, FR, IT, ES, CA, JP)
- **category** (string): Product category
- **brand** (string): Product brand name
- **rating** (float): Average customer rating (0-5)
- **review_count** (integer): Total number of reviews
- **image_url** (string): Product image URL
- **product_url** (string): Amazon product page URL
- **is_active** (boolean): Whether product tracking is active
- **created_at** (datetime): Product creation timestamp
- **updated_at** (datetime): Last update timestamp

## Related Data

- **Price Snapshots**: Historical price data points
- **Sales Snapshots**: Historical BSR and sales data
- **Competitors**: Related competitor products
- **Alerts**: Configured alert rules
- **Optimization Suggestions**: AI-generated recommendations
"""
