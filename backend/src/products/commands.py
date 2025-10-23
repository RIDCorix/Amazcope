"""Product management commands."""

import asyncio
import random
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from core.database import get_async_db_context
from products.models import Product as Product
from products.models import ProductSnapshot as ProductSnapshot
from pydantic_commands import command


class GenerateHistoryArgs(BaseModel):
    """Arguments for generating product history."""

    days: int = Field(
        30,
        ge=1,
        le=365,
        description="Number of days of history to generate (default: 30)",
    )
    snapshots_per_day: int = Field(
        1, ge=1, le=24, description="Number of snapshots per day (default: 1)"
    )
    price_volatility: float = Field(
        0.05,
        ge=0.0,
        le=1.0,
        description="Price change volatility (0.0-1.0, default: 0.05 = ±5%)",
    )
    bsr_volatility: float = Field(
        0.15,
        ge=0.0,
        le=1.0,
        description="BSR change volatility (0.0-1.0, default: 0.15 = ±15%)",
    )


@command(
    name="generate-product-history",
    help="Generate mock historical snapshot data for all products",
    arguments=GenerateHistoryArgs,
)
def generate_product_history(args: GenerateHistoryArgs) -> None:
    """Generate mock historical ProductSnapshot data for testing and development.

    This command creates realistic time-series data for all products in the database,
    simulating daily price changes, BSR fluctuations, review growth, and more.

    Example usage:
        python cli.py generate-product-history --days 30
        python cli.py generate-product-history --days 90 --snapshots-per-day 2
        python cli.py generate-product-history --days 7 --price-volatility 0.10
    """

    async def _generate_history() -> None:
        # Get all products using SQLAlchemy
        async with get_async_db_context() as db:
            stmt = select(Product)
            result = await db.execute(stmt)
            products = result.scalars().all()

            if not products:
                print("❌ No products found in database. Please add products first.")
                return

            print(f"\n📊 Generating {args.days} days of history for {len(products)} product(s)...")
            print(f"   Snapshots per day: {args.snapshots_per_day}")
            print(f"   Price volatility: {args.price_volatility * 100:.1f}%")
            print(f"   BSR volatility: {args.bsr_volatility * 100:.1f}%\n")

            total_snapshots = 0

            for product in products:
                print(f"🔄 Processing: {product.title[:50]}...")

                # Get product's current data as baseline
                # Try to get latest snapshot for baseline price
                stmt = (
                    select(ProductSnapshot)
                    .where(ProductSnapshot.product_id == product.id)
                    .order_by(ProductSnapshot.scraped_at.desc())
                    .limit(1)
                )
                result = await db.execute(stmt)
                latest_snapshot = result.scalar_one_or_none()

                if latest_snapshot and latest_snapshot.price:
                    base_price = float(latest_snapshot.price)
                else:
                    # Generate random price based on category (rough estimates)
                    base_price = round(random.uniform(19.99, 99.99), 2)

                base_bsr = random.randint(1000, 100000)  # Random initial BSR
                base_rating = 4.0 + random.random()  # 4.0 - 5.0
                base_reviews = random.randint(50, 5000)

                snapshots_created = 0

                # Generate snapshots going backwards in time
                for day in range(args.days):
                    date_offset = args.days - day  # Start from oldest
                    snapshot_date = datetime.utcnow() - timedelta(days=date_offset)

                    for snapshot_num in range(args.snapshots_per_day):
                        # Add time variation within the day
                        hours_offset = (24 / args.snapshots_per_day) * snapshot_num
                        snapshot_datetime = snapshot_date + timedelta(hours=hours_offset)

                        # Generate price with trend and volatility
                        # Prices tend to decrease over time (simulating deals/competition)
                        trend_factor = 1.0 - (day / args.days) * 0.1  # Up to 10% decrease
                        volatility_factor = 1.0 + random.uniform(
                            -args.price_volatility, args.price_volatility
                        )
                        current_price = round(base_price * trend_factor * volatility_factor, 2)

                        # Generate BSR with volatility (lower is better)
                        bsr_volatility_factor = 1.0 + random.uniform(
                            -args.bsr_volatility, args.bsr_volatility
                        )
                        current_bsr = int(base_bsr * bsr_volatility_factor)
                        current_bsr = max(1, min(current_bsr, 999999))  # Keep in valid range

                        # Simulate review growth over time
                        review_growth = int((day / args.days) * random.randint(10, 200))
                        current_reviews = base_reviews + review_growth

                        # Rating gradually improves or stays stable
                        rating_change = random.uniform(-0.1, 0.2)
                        current_rating = max(3.0, min(5.0, base_rating + rating_change))

                        # Occasional out of stock
                        in_stock = random.random() > 0.05  # 95% in stock

                        # Create snapshot using SQLAlchemy
                        snapshot = ProductSnapshot(
                            product_id=product.id,
                            scraped_at=snapshot_datetime,
                            # Price data
                            price=current_price,
                            original_price=round(current_price * 1.2, 2),  # 20% markup
                            buybox_price=current_price,
                            currency="USD",  # Default currency
                            discount_percentage=round(
                                (1 - current_price / (current_price * 1.2)) * 100, 2
                            ),
                            # BSR data
                            bsr_main_category=current_bsr,
                            bsr_small_category=int(
                                current_bsr * 0.7
                            ),  # Sub-category has lower rank
                            main_category_name=product.category or "Electronics",
                            small_category_name=(product.small_category or "Consumer Electronics"),
                            # Rating & Reviews
                            rating=round(current_rating, 1),
                            review_count=current_reviews,
                            # Availability
                            in_stock=in_stock,
                            stock_quantity=random.randint(0, 50) if in_stock else 0,
                            stock_status="In Stock" if in_stock else "Out of Stock",
                            # Seller info
                            seller_name=random.choice(
                                ["Amazon.com", "TechStore", "BestBuy", "SuperDeals"]
                            ),
                            is_amazon_seller=random.random() > 0.5,
                            is_fba=random.random() > 0.3,
                            is_prime=random.random() > 0.2,
                            # Deals
                            is_deal=random.random() > 0.8,  # 20% of time on deal
                            coupon_available=random.random() > 0.9,  # 10% have coupons
                            # Amazon's Choice
                            has_amazons_choice=random.random() > 0.85,  # 15% are Amazon's Choice
                        )
                        db.add(snapshot)
                        snapshots_created += 1

                # Commit all snapshots for this product
                await db.commit()
                print(f"   ✅ Created {snapshots_created} snapshots for '{product.title[:40]}...'")
                total_snapshots += snapshots_created

            print(f"\n🎉 Successfully generated {total_snapshots} total snapshots!")
            print(f"   Products processed: {len(products)}")
            print(f"   Average snapshots per product: {total_snapshots / len(products):.1f}")
            print(f"   Date range: {args.days} days")
            print("\n💡 You can now use the metrics API to view trends and analytics!")

    # Run async function
    asyncio.run(_generate_history())


class ClearHistoryArgs(BaseModel):
    """Arguments for clearing product history."""

    confirm: bool = Field(False, description="Confirm deletion of all snapshots (required)")


@command(
    name="clear-product-history",
    help="Delete all product snapshot history (DESTRUCTIVE)",
    arguments=ClearHistoryArgs,
)
def clear_product_history(args: ClearHistoryArgs) -> None:
    """Delete all ProductSnapshot records from the database.

    ⚠️  WARNING: This is a destructive operation and cannot be undone!

    Example usage:
        python cli.py clear-product-history --confirm
    """

    async def _clear_history() -> None:
        if not args.confirm:
            print("❌ Error: You must pass --confirm flag to delete all snapshots")
            print("   Example: python cli.py clear-product-history --confirm")
            return

        # Count existing snapshots using SQLAlchemy
        async with get_async_db_context() as db:
            stmt = select(func.count()).select_from(ProductSnapshot)
            result = await db.execute(stmt)
            count = result.scalar_one()

            if count == 0:
                print("ℹ️  No snapshots found in database.")
                return

            # Confirm again
            print(f"\n⚠️  WARNING: About to delete {count} snapshot records!")
            response = input("Type 'DELETE' to confirm: ")

            if response != "DELETE":
                print("❌ Deletion cancelled.")
                return

            # Delete all snapshots using SQLAlchemy
            stmt = delete(ProductSnapshot)
            await db.execute(stmt)
            await db.commit()

            print(f"\n✅ Successfully deleted {count} snapshot records!")

    # Run async function
    asyncio.run(_clear_history())
