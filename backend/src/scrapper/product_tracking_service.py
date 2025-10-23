"""Product tracking service for managing Amazcopeing."""

import logging
from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException, status
from sentry_sdk import capture_exception
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alert.models import Alert
from core.utils import trans_error_message
from products.models import (
    Product,
    ProductSnapshot,
    UserProduct,
)
from schemas.scraper_response import NormalizedProductResponse
from services.apify_service import ApifyService
from services.cache_service import CacheService
from users.models import User

logger = logging.getLogger(__name__)


class ProductTrackingService:
    """Service for tracking Amazon products and detecting changes."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize tracking service.

        Args:
            db: SQLAlchemy async database session
        """
        self.db = db
        self.apify_service = ApifyService()
        self.cache_service = CacheService()

    async def add_product_from_url(
        self,
        user_id: UUID,
        amazon_url: str,
        price_threshold: float = 10.0,
        bsr_threshold: float = 30.0,
        scrape_reviews: bool = True,
        scrape_bestsellers: bool = True,
        category_url: str | None = None,
        manual_category: str | None = None,
        manual_small_category: str | None = None,
    ) -> Product:
        """Add a new product to track from Amazon URL.

        This method will:
        1. Extract ASIN from URL
        2. Create product record in database
        3. Start background job to scrape product details
        4. Start background job to scrape reviews (if enabled)
        5. Start background job to scrape bestsellers in category (if enabled)

        Args:
            user_id: User ID who owns this product
            amazon_url: Amazon product URL
            price_threshold: Alert threshold for price changes (%)
            bsr_threshold: Alert threshold for BSR changes (%)
            scrape_reviews: Whether to scrape product reviews
            scrape_bestsellers: Whether to scrape category bestsellers
            category_url: Custom category URL (overrides auto-detected)
            manual_category: Manually specified category name
            manual_small_category: Manually specified subcategory name

        Returns:
            Created Product instance

        Raises:
            HTTPException: If URL is invalid or product already exists
        """
        # Extract ASIN and marketplace from URL
        asin = self.apify_service.extract_asin_from_url(amazon_url)
        if not asin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not extract ASIN from URL: {amazon_url}",
            )

        marketplace = self.apify_service.extract_marketplace_from_url(amazon_url)
        logger.info(f"Extracted ASIN {asin} and marketplace {marketplace} from URL: {amazon_url}")

        # Check if product already exists for this user in this marketplace
        result = await self.db.execute(
            select(Product).where(Product.asin == asin, Product.marketplace == marketplace)
        )
        existing_product = result.scalar_one_or_none()

        if existing_product:
            # Check if user already has this product
            result = await self.db.execute(
                select(UserProduct).where(
                    UserProduct.user_id == user_id,
                    UserProduct.product_id == existing_product.id,
                )
            )
            existing_user_product = result.scalar_one_or_none()

            if existing_user_product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {asin} already being tracked",
                )

            # Product exists but user doesn't have it, create UserProduct relationship
            user_product = UserProduct(
                user_id=user_id,
                product_id=existing_product.id,
                price_change_threshold=price_threshold,
                bsr_change_threshold=bsr_threshold,
            )
            self.db.add(user_product)
            await self.db.commit()
            logger.info(f"User {user_id} claimed existing product {asin}")
            return existing_product

        # Scrape initial product data synchronously (to get basic info for DB record)
        logger.info(f"Scraping initial data for ASIN: {asin} in marketplace: {marketplace}")
        product_data = await self.apify_service.scrape_product(asin, marketplace=marketplace)

        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to scrape product data for ASIN: {asin}",
            )

        # Check if product is 404 (dict response)
        if isinstance(product_data, dict):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {asin} not found on Amazon (404)",
            )

        # Use manual categories if provided, otherwise use scraped data
        final_category = manual_category or product_data.main_category_name
        final_small_category = manual_small_category or product_data.small_category_name

        # Determine category URL: custom > scraped > None
        final_category_url = category_url or getattr(product_data, "category_url", None)

        # Create product record
        product = Product(
            asin=asin,
            marketplace=marketplace,
            title=product_data.title,
            brand=product_data.brand,
            category=final_category,
            small_category=final_small_category,
            url=amazon_url,  # Use the original URL provided
            image_url=product_data.image_url,
            bsr_category_link=final_category_url,  # Store category URL in bsr_category_link
            price_change_threshold=price_threshold,
            bsr_change_threshold=bsr_threshold,
            rating=product_data.rating if hasattr(product_data, "rating") else None,
            review_count=product_data.review_count
            if hasattr(product_data, "review_count")
            else None,
            is_active=True,
            created_by_id=user_id,
        )
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)

        # Create UserProduct relationship
        user_product = UserProduct(
            user_id=user_id,
            product_id=product.id,
            price_change_threshold=price_threshold,
            bsr_change_threshold=bsr_threshold,
        )
        self.db.add(user_product)
        await self.db.commit()

        # Create initial snapshot
        await self._create_snapshot(product, product_data)

        # Start background jobs
        from products.tasks import scrape_category_bestsellers

        # Schedule bestsellers scraping if enabled and category URL is available
        if scrape_bestsellers and final_category_url:
            # Trigger Dramatiq task to scrape category bestsellers
            scrape_category_bestsellers.send(category_url=final_category_url, max_items=50)
            logger.info(f"Scheduled bestsellers scraping task for category: {final_category}")

        logger.info(f"Successfully added product {asin} for user {user_id}")
        return product

    async def update_product(self, product_id: UUID, check_alerts: bool = True) -> ProductSnapshot:
        """Update product data by scraping latest information.

        Args:
            product_id: Product ID to update
            check_alerts: Whether to check for alert conditions

        Returns:
            Created ProductSnapshot

        Raises:
            HTTPException: If product not found or scraping fails
        """
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )

        # Check cache first (avoid excessive scraping)
        cache_key = f"product_snapshot:{product.asin}"
        cached_data = await self.cache_service.get(cache_key)

        if cached_data:
            logger.info(f"Using cached data for ASIN: {product.asin}")
            return cast(ProductSnapshot, cached_data)

        # Scrape latest data
        logger.info(f"Updating product data for ASIN: {product.asin}")
        product_data = await self.apify_service.scrape_product(
            product.asin, marketplace=product.marketplace
        )

        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update product {product.asin}",
            )

        # Check if product returned 404 (unlisted)
        if isinstance(product_data, dict) and product_data.get("status") == "404":
            logger.warning(f"Product {product.asin} returned 404 - marking as unlisted")

            # Mark product as unlisted
            from datetime import datetime

            product.is_unlisted = True
            product.unlisted_at = datetime.utcnow()
            product.is_active = False  # Stop tracking unlisted products
            await self.db.commit()

            # Return a minimal snapshot or raise exception
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product.asin} is no longer available on Amazon (404)",
            )

        # Create new snapshot
        snapshot = await self._create_snapshot(product, product_data)

        # Cache snapshot for 24 hours
        await self.cache_service.set(cache_key, snapshot, ttl=86400)

        return snapshot

    async def batch_update_products(self, product_ids: list[UUID]) -> dict[str, Any]:
        """Update multiple products in batch.

        Args:
            product_ids: List of product IDs to update

        Returns:
            Summary dict with success/failure counts
        """
        logger.info(f"Starting batch update for {len(product_ids)} products")

        results: dict[str, Any] = {"success": 0, "failed": 0, "errors": []}

        for product_id in product_ids:
            try:
                await self.update_product(product_id, check_alerts=True)
                results["success"] += 1
            except Exception as e:
                capture_exception(e)
                results["failed"] += 1
                results["errors"].append({"product_id": product_id, "error": str(e)})
                logger.error(f"Failed to update product {product_id}: {trans_error_message(e)}")

        logger.info(f"Batch update completed: {results['success']}/{len(product_ids)} successful")
        return results

    async def refresh_product(
        self, product_id: UUID, update_metadata: bool = True, check_alerts: bool = True
    ) -> ProductSnapshot:
        """Force real-time product refresh (bypasses cache).

        This method:
        1. Scrapes fresh data from Amazon
        2. Creates new snapshot
        3. Optionally updates product metadata fields
        4. Checks for alerts

        Args:
            product_id: Product ID to refresh
            update_metadata: Whether to update product base fields (title, features, etc.)
            check_alerts: Whether to check for alert conditions

        Returns:
            Created ProductSnapshot with fresh data

        Raises:
            HTTPException: If product not found or scraping fails
        """
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )

        # Scrape fresh data (no cache)
        logger.info(f"Force refreshing product data for ASIN: {product.asin}")
        product_data = await self.apify_service.scrape_product(
            product.asin, marketplace=product.marketplace
        )

        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to scrape product {product.asin}",
            )

        # Check if product returned 404 (unlisted)
        if isinstance(product_data, dict) and product_data.get("status") == "404":
            logger.warning(f"Product {product.asin} returned 404 - marking as unlisted")

            # Mark product as unlisted
            from datetime import datetime

            product.is_unlisted = True
            product.unlisted_at = datetime.utcnow()
            product.is_active = False  # Stop tracking unlisted products
            await self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product.asin} is no longer available on Amazon (404)",
            )

        # Update product metadata if requested
        if update_metadata:
            await self._update_product_metadata(product, product_data)

        # Create new snapshot
        snapshot = await self._create_snapshot(product, product_data)

        # Clear cache to ensure fresh data on next request
        cache_key = f"product_snapshot:{product.asin}"
        await self.cache_service.delete(cache_key)

        logger.info(f"Successfully refreshed product {product.asin}")
        return snapshot

    async def batch_refresh_products(
        self, product_ids: list[UUID], update_metadata: bool = True
    ) -> dict[str, Any]:
        """Force real-time refresh for multiple products (bypasses cache).

        Args:
            product_ids: List of product IDs to refresh
            update_metadata: Whether to update product metadata fields

        Returns:
            Summary dict with success/failure counts and detailed results
        """
        logger.info(f"Starting batch refresh for {len(product_ids)} products")

        results: dict[str, Any] = {
            "success": 0,
            "failed": 0,
            "errors": [],
            "updated_products": [],
        }

        for product_id in product_ids:
            try:
                snapshot = await self.refresh_product(
                    product_id,
                    update_metadata=update_metadata,
                    check_alerts=True,
                )
                results["success"] += 1
                results["updated_products"].append(
                    {
                        "product_id": product_id,
                        "snapshot_id": snapshot.id,
                        "scraped_at": snapshot.scraped_at.isoformat(),
                    }
                )
                logger.info(f"Successfully refreshed product {product_id}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"product_id": product_id, "error": str(e)})
                logger.error(f"Failed to refresh product {product_id}: {str(e)}")

        logger.info(f"Batch refresh completed: {results['success']}/{len(product_ids)} successful")
        return results

    async def _update_product_metadata(self, product: Product, product_data: Any) -> None:
        """Update product base fields with latest data.

        Args:
            product: Product instance to update
            product_data: Pydantic model instance
        """
        # Basic info
        if getattr(product_data, "title", None):
            product.title = product_data.title
        if getattr(product_data, "brand", None):
            product.brand = product_data.brand
        if getattr(product_data, "manufacturer", None):
            product.manufacturer = product_data.manufacturer

        # Categories
        if getattr(product_data, "main_category_name", None):
            product.category = product_data.main_category_name
        if getattr(product_data, "small_category_name", None):
            product.small_category = product_data.small_category_name

        # BSR links
        if getattr(product_data, "bsr_category_link", None):
            product.bsr_category_link = product_data.bsr_category_link
        if getattr(product_data, "bsr_subcategory_link", None):
            product.bsr_subcategory_link = product_data.bsr_subcategory_link

        # Amazon's Choice
        if getattr(product_data, "amazons_choice_keywords", None) is not None:
            product.amazons_choice_keywords = product_data.amazons_choice_keywords
            product.has_amazons_choice = getattr(product_data, "has_amazons_choice", False)

        # Specifications
        if getattr(product_data, "product_dimensions", None):
            product.product_dimensions = product_data.product_dimensions
        if getattr(product_data, "item_weight", None):
            product.item_weight = product_data.item_weight
        if getattr(product_data, "model_number", None):
            product.model_number = product_data.model_number

        # Variations
        if getattr(product_data, "has_variations", None) is not None:
            product.has_variations = product_data.has_variations
        if getattr(product_data, "variation_types", None):
            product.variation_types = product_data.variation_types
        if getattr(product_data, "total_variations", None) is not None:
            product.total_variations = product_data.total_variations

        # Content
        if getattr(product_data, "seller_store_url", None):
            product.seller_store_url = product_data.seller_store_url
        if getattr(product_data, "product_description", None):
            product.product_description = product_data.product_description
        if getattr(product_data, "features", None):
            product.features = product_data.features
        if getattr(product_data, "product_overview", None):
            product.product_overview = product_data.product_overview
        if getattr(product_data, "technical_details", None):
            product.technical_details = product_data.technical_details

        # Image URL (in case it changes)
        if getattr(product_data, "image_url", None):
            product.image_url = product_data.image_url

        # Rating (update with latest from snapshot)
        if getattr(product_data, "rating", None) is not None:
            product.rating = product_data.rating

        # Review count (update with latest from snapshot)
        if getattr(product_data, "review_count", None) is not None:
            product.review_count = product_data.review_count

        await self.db.commit()
        logger.info(f"Updated metadata for product {product.asin}")

    async def get_product_history(self, product_id: UUID, days: int = 30) -> list[ProductSnapshot]:
        """Get product snapshot history.

        Args:
            product_id: Product ID
            days: Number of days to retrieve (default 30)

        Returns:
            List of ProductSnapshot instances
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(ProductSnapshot)
            .where(
                ProductSnapshot.product_id == product_id,
                ProductSnapshot.scraped_at >= since_date,
            )
            .order_by(ProductSnapshot.scraped_at.desc())
        )
        snapshots = result.scalars().all()

        return list(snapshots)

    async def update_product_category(
        self,
        product_id: UUID,
        category_url: str | None = None,
        manual_category: str | None = None,
        manual_small_category: str | None = None,
        trigger_bestsellers_scrape: bool = True,
    ) -> Product:
        """Update product category information.

        Args:
            product_id: Product ID to update
            category_url: New category URL
            manual_category: Manual category name
            manual_small_category: Manual subcategory name
            trigger_bestsellers_scrape: Whether to trigger bestsellers scraping

        Returns:
            Updated Product instance

        Raises:
            HTTPException: If product not found
        """
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product: Product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )

        # Update fields if provided
        if manual_category is not None:
            product.category = manual_category
        if manual_small_category is not None:
            product.small_category = manual_small_category
        if category_url is not None:
            product.bsr_category_link = category_url

        await self.db.commit()
        await self.db.refresh(product)
        logger.info(f"Updated category for product {product.asin}")

        # Trigger bestsellers scraping if requested and category URL provided
        if trigger_bestsellers_scrape and category_url:
            from products.tasks import scrape_category_bestsellers

            scrape_category_bestsellers.send(category_url=category_url, max_items=50)
            logger.info(f"Scheduled bestsellers scraping for updated category: {category_url}")

        return product

    async def get_product_alerts(self, product_id: UUID, unread_only: bool = False) -> list[Alert]:
        """Get alerts for a product.

        Args:
            product_id: Product ID
            unread_only: Whether to return only unread alerts

        Returns:
            List of Alert instances
        """
        query = select(Alert).where(Alert.product_id == product_id)

        if unread_only:
            query = query.where(Alert.is_read == False)  # noqa: E712

        query = query.order_by(Alert.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _create_snapshot(
        self, product: Product, product_data: NormalizedProductResponse
    ) -> ProductSnapshot:
        """Create a product snapshot from scraped data.

        Args:
            product: Product instance
            product_data: Pydantic model instance

        Returns:
            Created ProductSnapshot instance
        """
        snapshot = ProductSnapshot(
            product_id=product.id,
            price=product_data.price,
            original_price=product_data.original_price,
            buybox_price=product_data.buybox_price,
            currency=product_data.currency,
            discount_percentage=product_data.discount_percentage,
            bsr_main_category=product_data.bsr_main_category,
            bsr_small_category=product_data.bsr_small_category,
            main_category_name=product_data.main_category_name,
            small_category_name=product_data.small_category_name,
            rating=product_data.rating,
            review_count=product_data.review_count,
            in_stock=product_data.in_stock,
            stock_quantity=product_data.stock_quantity,
            seller_name=product_data.seller_name,
            is_amazon_seller=product_data.is_amazon_seller,
            is_fba=product_data.is_fba,
            coupon_text=product_data.coupon_text,
            deal_type=product_data.deal_type,
            # Enhanced metadata fields (Phase 2)
            amazons_choice_keywords=getattr(product_data, "amazons_choice_keywords", None),
            has_amazons_choice=getattr(product_data, "has_amazons_choice", False),
            past_sales=getattr(product_data, "past_sales", None),
            delivery_message=getattr(product_data, "delivery_message", None),
            product_type=getattr(product_data, "product_type", None),
            is_used=getattr(product_data, "is_used", False),
            seller_id=getattr(product_data, "seller_id", None),
            seller_store_url=getattr(product_data, "seller_store_url", None),
            fulfilled_by=getattr(product_data, "fulfilled_by", None),
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)

        # Update denormalized fields in Product table for performance
        product.current_price = product_data.price
        product.original_price = product_data.original_price
        product.currency = product_data.currency or "USD"
        product.discount_percentage = product_data.discount_percentage
        product.current_bsr = product_data.bsr_main_category
        product.bsr_category_name = product_data.main_category_name
        product.in_stock = product_data.in_stock if product_data.in_stock is not None else True
        product.stock_status = "In Stock" if product_data.in_stock else "Out of Stock"
        product.is_prime = False  # TODO: Add is_prime to NormalizedProductResponse
        product.seller_name = product_data.seller_name
        product.is_amazon_seller = product_data.is_amazon_seller or False
        product.is_fba = product_data.is_fba or False
        product.last_snapshot_at = snapshot.scraped_at
        product.rating = product_data.rating
        product.review_count = product_data.review_count

        await self.db.commit()
        await self.db.refresh(product)

        # Check and create alerts after snapshot creation
        await self._check_and_create_alerts(product, snapshot)

        return snapshot

    async def _check_and_create_alerts(self, product: Product, snapshot: ProductSnapshot) -> None:
        """Check for alert conditions and create alerts if thresholds exceeded.

        Args:
            product: Product instance
            snapshot: Latest snapshot
        """
        # Get previous snapshot for comparison
        result = await self.db.execute(
            select(ProductSnapshot)
            .where(
                ProductSnapshot.product_id == product.id,
                ProductSnapshot.id < snapshot.id,  # Get snapshot before current one
            )
            .order_by(ProductSnapshot.scraped_at.desc())
            .limit(1)
        )
        previous_snapshot = result.scalar_one_or_none()

        if not previous_snapshot:
            logger.info(f"No previous snapshot for product {product.asin}, skipping alert check")
            return

        # Get user who created this product
        if not product.created_by_id:
            logger.info(f"No user associated with product {product.asin}, skipping alerts")
            return

        # Load user if not already loaded
        result = await self.db.execute(select(User).where(User.id == product.created_by_id))
        user = result.scalar_one_or_none()
        if not user:
            logger.info(f"User not found for product {product.asin}, skipping alerts")
            return

        # Check price changes
        if snapshot.price and previous_snapshot.price:
            price_change_pct = snapshot.calculate_price_change_percentage(previous_snapshot.price)

            if price_change_pct and abs(price_change_pct) >= product.price_change_threshold:
                price_alert = Alert(
                    product_id=product.id,
                    snapshot_id=snapshot.id,
                    user_id=user.id,
                    alert_type="price_change",
                    severity="warning" if abs(price_change_pct) < 20 else "critical",
                    title=f"Price {'increased' if price_change_pct > 0 else 'decreased'} by {abs(price_change_pct):.1f}%",
                    message=f"Price changed from {product.currency}{previous_snapshot.price:.2f} to {product.currency}{snapshot.price:.2f}",
                    old_value=str(previous_snapshot.price),
                    new_value=str(snapshot.price),
                    change_percentage=price_change_pct,
                )
                self.db.add(price_alert)
                logger.info(
                    f"Created price alert for product {product.asin}: {price_change_pct:.1f}%"
                )

        # Check BSR changes (small category)
        if snapshot.bsr_small_category and previous_snapshot.bsr_small_category:
            bsr_change_pct = snapshot.calculate_bsr_change_percentage(previous_snapshot, "small")

            if bsr_change_pct and abs(bsr_change_pct) >= product.bsr_change_threshold:
                bsr_alert = Alert(
                    product_id=product.id,
                    snapshot_id=snapshot.id,
                    user_id=user.id,
                    alert_type="bsr_change",
                    severity="info" if abs(bsr_change_pct) < 30 else "warning",
                    title=f"BSR {'improved' if bsr_change_pct < 0 else 'declined'} by {abs(bsr_change_pct):.1f}%",
                    message=f"BSR changed from #{previous_snapshot.bsr_small_category} to #{snapshot.bsr_small_category} in {snapshot.small_category_name or 'small category'}",
                    old_value=str(previous_snapshot.bsr_small_category),
                    new_value=str(snapshot.bsr_small_category),
                    change_percentage=bsr_change_pct,
                )
                self.db.add(bsr_alert)
                logger.info(f"Created BSR alert for product {product.asin}: {bsr_change_pct:.1f}%")

        # Check stock status changes
        if snapshot.in_stock != previous_snapshot.in_stock:
            alert_type = "back_in_stock" if snapshot.in_stock else "out_of_stock"
            stock_alert = Alert(
                product_id=product.id,
                snapshot_id=snapshot.id,
                user_id=user.id,
                alert_type=alert_type,
                severity="critical" if not snapshot.in_stock else "info",
                title=f"Product {'back in stock' if snapshot.in_stock else 'out of stock'}",
                message=f"Stock status changed for {product.title}",
                old_value=str(previous_snapshot.in_stock),
                new_value=str(snapshot.in_stock),
            )
            self.db.add(stock_alert)
            logger.info(f"Created stock alert for product {product.asin}")

        # Commit all alerts at once
        await self.db.commit()
