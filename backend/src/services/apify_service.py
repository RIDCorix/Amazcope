"""Apify service for scraping Amazon product data."""

import logging
from typing import Any

from apify_client import ApifyClientAsync

from core.config import settings
from products.models import Product
from schemas.apify_schemas import ApifyProductResponse
from schemas.scraper_response import (
    NormalizedProductResponse,
    ProductOverviewDetail,
    ProductTechnicalDetail,
)

logger = logging.getLogger(__name__)


class ApifyService:
    """Service for interacting with Apify API to scrape Amazon product data."""

    # Apify Actor IDs
    PRODUCT_SCRAPER = "axesso_data/amazon-product-details-scraper"
    REVIEW_SCRAPER = "axesso_data/amazon-reviews-scraper"
    BESTSELLER_SCRAPER = "junglee/amazon-bestsellers"

    def __init__(self) -> None:
        """Initialize Apify client with API token from settings."""
        if not settings.APIFY_API_TOKEN:
            raise ValueError("APIFY_API_TOKEN not configured")

        self.client = ApifyClientAsync(token=settings.APIFY_API_TOKEN)

    async def scrape_product(
        self, asin: str, marketplace: str = "com"
    ) -> NormalizedProductResponse:
        """Scrape single product data from Amazon.

        Args:
            asin: Amazon Standard Identification Number
            marketplace: Amazon marketplace (e.g., 'com', 'co.uk', 'de')

        Returns:
            NormalizedProductResponse, dict with 404 status, or None if scraping failed
        """
        # Use batch scraper with single ASIN
        results = await self.scrape_products_batch([asin], marketplace=marketplace)
        if not results:
            logger.error(f"No results returned for ASIN: {asin}")
            raise ValueError(f"No results returned for ASIN: {asin}")
        return results[asin]

    async def scrape_products_batch(
        self, asins: list[str], marketplace: str = "com"
    ) -> dict[str, NormalizedProductResponse]:
        """Scrape multiple products in batches.

        Args:
            asins: List of Amazon ASINs to scrape
            marketplace: Amazon marketplace (e.g., 'com', 'co.uk', 'de')

        Returns:
            Dict mapping ASIN to NormalizedProductResponse or dict with 404 status
        """
        logger.info(f"Starting batch scrape for {len(asins)} products in amazon.{marketplace}")

        all_results: dict[str, NormalizedProductResponse] = {}
        batch_size = 100

        # Process ASINs in batches of 100
        for i in range(0, len(asins), batch_size):
            batch_asins = asins[i : i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}: {len(batch_asins)} ASINs")

            try:
                # Convert ASINs to URLs for Apify API with correct marketplace
                batch_urls = [
                    self._asin_to_url(asin, domain=f"amazon.{marketplace}") for asin in batch_asins
                ]

                # Configure actor input for this batch
                run_input = {
                    "urls": batch_urls,
                }

                # Run the actor and wait for results
                run = await self.client.actor(self.PRODUCT_SCRAPER).call(run_input=run_input)
                assert run is not None, "Apify actor run returned None"

                # Fetch results from dataset
                async for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                    try:
                        # Parse with Pydantic model
                        product_response = ApifyProductResponse(**item)

                        # Check for 404 status (product not found/unlisted)
                        if product_response.status_code == 404:
                            # Extract ASIN from URL if not in response
                            asin = product_response.asin
                            if not asin:
                                # Try to extract from URL
                                import re

                                url_match = re.search(r"/dp/([A-Z0-9]{10})", product_response.url)
                                if url_match:
                                    asin = url_match.group(1)

                            if asin:
                                logger.warning(f"Product {asin} returned 404 - marking as unlisted")
                            else:
                                logger.warning(
                                    f"Product returned 404 but no ASIN found in URL: {product_response.url}"
                                )
                        elif product_response.asin and product_response.title:
                            # Only normalize if we have essential data
                            all_results[product_response.asin] = self._normalize_product_data(
                                product_response
                            )
                        else:
                            logger.warning(
                                f"Product data missing essential fields (asin or title): {product_response.url}"
                            )
                    except Exception as parse_error:
                        logger.warning(f"Failed to parse product data: {parse_error}")
                        continue

                logger.info(
                    f"Batch {i // batch_size + 1} completed: {len(all_results)} total products scraped"
                )

            except Exception as e:
                logger.error(f"Error scraping batch {i // batch_size + 1}: {str(e)}")
                continue

        logger.info(f"Batch scrape completed: {len(all_results)}/{len(asins)} successful")
        return all_results

    async def scrape_reviews(
        self, url: str, max_reviews: int = 100, sort_by: str = "recent"
    ) -> list[dict[str, Any]]:
        """Scrape product reviews from Amazon.

        Args:
            url: Amazon product URL
            max_reviews: Maximum number of reviews to scrape (default 100)
            sort_by: Sort order - 'recent', 'helpful', 'top_reviews' (default 'recent')

        Returns:
            List of review dicts
        """
        try:
            logger.info(f"Starting review scrape for URL: {url}")

            # Configure actor input
            run_input = {
                "startUrls": [{"url": url}],
                "maxReviews": max_reviews,
                "sortBy": sort_by,
                "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
            }

            # Run the actor
            run = await self.client.actor(self.REVIEW_SCRAPER).call(run_input=run_input)
            assert run is not None, "Apify actor run returned None"

            # Fetch results
            reviews = []
            async for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                reviews.append(self._normalize_review_data(item))

            logger.info(f"Successfully scraped {len(reviews)} reviews for URL: {url}")
            return reviews

        except Exception as e:
            logger.error(f"Error scraping reviews for URL {url}: {str(e)}")
            return list()  # type: ignore[return-value]

    async def scrape_bestsellers(
        self, category_url: str, max_items: int = 100
    ) -> list[dict[str, Any]]:
        """Scrape bestsellers from Amazon category.

        Args:
            category_url: Amazon category/bestsellers URL
            max_items: Maximum number of products to scrape (default 100)

        Returns:
            List of bestseller items (raw data from Apify)

        Raises:
            Exception: If scraping fails or no data returned
        """
        logger.info(f"Starting bestsellers scrape for URL: {category_url}")

        # Configure actor input
        run_input = {
            "categoryUrls": [category_url],
            "maxItems": max_items,
            "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        }

        # Run the actor
        run = await self.client.actor(self.BESTSELLER_SCRAPER).call(run_input=run_input)
        assert run is not None, "Apify actor run returned None"

        # Fetch results
        items = []
        async for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            items.append(item)

        if not items:
            logger.warning(f"No bestsellers data returned for URL: {category_url}")
            raise ValueError(f"No bestsellers data returned for URL: {category_url}")

        logger.info(f"Successfully scraped {len(items)} bestsellers")
        return items

    @staticmethod
    def _asin_to_url(asin: str, domain: str = "amazon.com") -> str:
        """Convert ASIN to Amazon product URL.

        Args:
            asin: Amazon Standard Identification Number
            domain: Amazon domain (default: amazon.com)

        Returns:
            Amazon product URL
        """
        return f"https://www.{domain}/dp/{asin}"

    @staticmethod
    def extract_marketplace_from_url(url: str) -> str:
        """Extract Amazon marketplace from URL.

        Args:
            url: Amazon product URL

        Returns:
            Marketplace code (e.g., 'com', 'co.uk', 'de', 'fr', 'it', 'es', 'ca', 'com.mx', 'co.jp', 'in', 'com.au')
            Defaults to 'com' if no valid marketplace found

        Examples:
            >>> extract_marketplace_from_url("https://www.amazon.com/dp/B01ABCD123")
            'com'
            >>> extract_marketplace_from_url("https://www.amazon.co.uk/dp/B01ABCD123")
            'co.uk'
            >>> extract_marketplace_from_url("https://www.amazon.de/dp/B01ABCD123")
            'de'
        """
        import re

        # Extract domain from URL
        domain_pattern = r"amazon\.([a-z.]+)"
        match = re.search(domain_pattern, url, re.IGNORECASE)

        if match:
            marketplace = match.group(1).lower()
            # Validate marketplace against known Amazon marketplaces
            valid_marketplaces = [
                "com",
                "co.uk",
                "de",
                "fr",
                "it",
                "es",
                "ca",
                "com.mx",
                "co.jp",
                "in",
                "com.au",
                "com.br",
                "nl",
                "sg",
                "ae",
                "sa",
                "se",
                "pl",
            ]
            if marketplace in valid_marketplaces:
                return marketplace

        # Default to .com if no valid marketplace found
        return "com"

    @staticmethod
    def extract_asin_from_url(url: str) -> str | None:
        """Extract ASIN from Amazon product URL.

        Args:
            url: Amazon product URL

        Returns:
            ASIN string or None if not found

        Examples:
            >>> extract_asin_from_url("https://www.amazon.com/dp/B01ABCD123")
            'B01ABCD123'
            >>> extract_asin_from_url("https://www.amazon.com/product-name/dp/B01ABCD123/")
            'B01ABCD123'
        """
        import re

        # Pattern to match ASIN in various Amazon URL formats
        patterns = [
            r"/dp/([A-Z0-9]{10})",  # /dp/ASIN
            r"/gp/product/([A-Z0-9]{10})",  # /gp/product/ASIN
            r"/product/([A-Z0-9]{10})",  # /product/ASIN
            r"[?&]asin=([A-Z0-9]{10})",  # ?asin=ASIN or &asin=ASIN
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        return None

    def _normalize_review_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize review data from Apify actor.

        Args:
            raw_data: Raw review data from actor

        Returns:
            Normalized review dict
        """
        from datetime import datetime

        # Parse review date
        review_date = raw_data.get("date")
        if isinstance(review_date, str):
            try:
                # Try parsing common date formats
                review_date = datetime.strptime(review_date, "%B %d, %Y")
            except ValueError:
                review_date = datetime.utcnow()
        elif not review_date:
            review_date = datetime.utcnow()

        return {
            "review_id": raw_data.get("reviewId") or raw_data.get("id"),
            "title": raw_data.get("title", ""),
            "text": raw_data.get("text", ""),
            "rating": float(raw_data.get("stars", 0) or raw_data.get("rating", 0)),
            "verified_purchase": raw_data.get("verifiedPurchase", False),
            "helpful_count": int(raw_data.get("helpful", 0) or 0),
            "review_date": review_date,
            "reviewer_name": raw_data.get("name") or raw_data.get("reviewerName"),
            "reviewer_id": raw_data.get("reviewerId"),
            "is_vine_voice": raw_data.get("isVine", False) or raw_data.get("vineVoice", False),
            "images": raw_data.get("images", []),
            "variant_info": raw_data.get("variant"),
        }

    def _normalize_bestsellers_data(
        self, items: list[dict[str, Any]]
    ) -> tuple[str, str, list[Product]]:
        """Normalize bestsellers data from Apify actor.

        Args:
            items: List of raw bestseller items

        Returns:
            Tuple of category name, category URL, and list of Product instances
        """
        if not items:
            return "", "", []

        # Extract category info from first item
        first_item = items[0]
        category_name: str = first_item.get("categoryName", "")
        category_url: str = first_item.get("url", "").split("/ref=")[0]  # Clean URL

        # Normalize each product
        bestsellers = []
        for item in items:
            bestsellers.append(
                Product(
                    rank=item.get("position") or item.get("rank"),
                    asin=item.get("asin"),
                    title=item.get("title"),
                    price=item.get("price", {}).get("value")
                    if isinstance(item.get("price"), dict)
                    else item.get("price"),
                    currency=item.get("currency", "USD"),
                    rating=item.get("stars") or item.get("rating"),
                    review_count=item.get("reviewsCount") or item.get("ratingsTotal", 0),
                    image_url=item.get("image") or item.get("thumbnailImage"),
                    url=item.get("url"),
                )
            )

        return category_name, category_url, bestsellers

    def _normalize_product_data(
        self, product_response: ApifyProductResponse
    ) -> NormalizedProductResponse:
        """Normalize Apify actor output to our standard format.

        Args:
            product_response: Parsed ApifyProductResponse from actor

        Returns:
            NormalizedProductResponse with all fields properly typed and validated
        """
        # Extract price information
        current_price = product_response.price
        original_price = product_response.retail_price
        buybox_price = (
            product_response.buy_box_used.price if product_response.buy_box_used else None
        )

        # Extract BSR information from bestSellersRank (new format) or categories_extended (old format)
        bsr_main = None
        bsr_small = None
        main_category = None
        small_category = None

        # Try new format first (bestSellersRank array)
        if product_response.best_sellers_rank and len(product_response.best_sellers_rank) > 0:
            # First BSR entry is usually the main category
            first_bsr = product_response.best_sellers_rank[0]
            try:
                bsr_main = int(first_bsr.rank.replace(",", "").strip())
                main_category = first_bsr.category_name
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse BSR rank: {first_bsr.rank}")

            # If there's a second BSR entry, it's the subcategory
            if len(product_response.best_sellers_rank) > 1:
                second_bsr = product_response.best_sellers_rank[1]
                try:
                    bsr_small = int(second_bsr.rank.replace(",", "").strip())
                    small_category = second_bsr.category_name
                except (ValueError, AttributeError):
                    logger.warning(f"Could not parse subcategory BSR rank: {second_bsr.rank}")

        # Fallback to old format (categories_extended)
        elif product_response.categories_extended:
            # First category is usually main category
            if len(product_response.categories_extended) > 0:
                main_category = product_response.categories_extended[0].name
            # Second category is usually subcategory
            if len(product_response.categories_extended) > 1:
                small_category = product_response.categories_extended[1].name

        # Calculate discount percentage
        discount_pct = None
        if current_price and original_price and original_price > current_price:
            discount_pct = ((original_price - current_price) / original_price) * 100

        # Parse rating from string like "4.7 out of 5 stars"
        rating = None
        if product_response.product_rating:
            try:
                rating = float(product_response.product_rating.split()[0])
            except (ValueError, IndexError):
                rating = None

        # Determine stock status
        in_stock = bool(
            product_response.warehouse_availability
            and "in stock" in product_response.warehouse_availability.lower()
            if product_response.warehouse_availability
            else False
        )

        # Extract seller information (new format has seller object)
        seller_name = None
        seller_store_url = None
        if product_response.seller and isinstance(product_response.seller, dict):
            seller_name = product_response.seller.get("name")
            seller_store_url = product_response.seller.get("url")
        if not seller_name:
            seller_name = product_response.sold_by

        # Check if it's Amazon as seller
        is_amazon = "amazon" in str(seller_name or "").lower()
        is_fba = (
            product_response.fulfilled_by == "Amazon" if product_response.fulfilled_by else False
        )

        # Extract BSR links
        bsr_main_link = None
        bsr_sub_link = None
        if product_response.best_sellers_rank:
            if len(product_response.best_sellers_rank) > 0:
                bsr_main_link = product_response.best_sellers_rank[0].link
            if len(product_response.best_sellers_rank) > 1:
                bsr_sub_link = product_response.best_sellers_rank[1].link

        # Check Amazon's Choice status
        has_amazons_choice = bool(
            product_response.amazons_choice_keywords
            and len(product_response.amazons_choice_keywords) > 0
        )

        # Extract product dimensions and weight
        item_weight = None
        model_number = None
        product_dimensions = {}
        if product_response.technical_details:
            for detail in product_response.technical_details:
                if detail.name.lower() == "item weight":
                    item_weight = detail.value
                elif detail.name.lower() == "item model number":
                    model_number = detail.value
                elif "dimension" in detail.name.lower():
                    product_dimensions[detail.name] = detail.value

        # Extract variation information
        has_variations = bool(product_response.variation_values)
        variation_types = (
            list(product_response.variation_values.keys())
            if product_response.variation_values
            else None
        )
        total_variations = len(product_response.dimensions) if product_response.dimensions else 0

        # Return validated Pydantic model instead of dict
        return NormalizedProductResponse(
            # Basic info
            asin=product_response.asin,
            title=product_response.title,
            brand=product_response.manufacturer,
            manufacturer=product_response.manufacturer,
            url=product_response.url,
            image_url=product_response.image_url_list[0]
            if product_response.image_url_list
            else None,
            # Product content
            product_description=product_response.product_description,
            features=product_response.features if product_response.features else None,
            product_overview=[
                ProductOverviewDetail(name=detail.name, value=detail.value)
                for detail in product_response.product_overview
            ]
            if product_response.product_overview
            else None,
            technical_details=[
                ProductTechnicalDetail(name=detail.name, value=detail.value)
                for detail in product_response.technical_details
            ]
            if product_response.technical_details
            else None,
            # Product specifications
            item_weight=item_weight,
            model_number=model_number,
            product_dimensions=product_dimensions if product_dimensions else None,
            # Price
            price=current_price,
            original_price=original_price,
            buybox_price=buybox_price,
            currency="USD",  # Default to USD, can be extracted from price_saving if needed
            discount_percentage=discount_pct,
            # BSR
            bsr_main_category=bsr_main,
            bsr_small_category=bsr_small,
            main_category_name=main_category,
            small_category_name=small_category,
            bsr_category_link=bsr_main_link,
            bsr_subcategory_link=bsr_sub_link,
            # Ratings & Reviews
            rating=rating,
            review_count=product_response.count_review,
            product_rating_text=product_response.product_rating,
            # Availability
            in_stock=in_stock,
            stock_quantity=None,  # Usually not available
            stock_status=product_response.warehouse_availability,
            # Seller info
            seller_name=seller_name,
            seller_id=product_response.seller_id,
            seller_store_url=seller_store_url,
            is_amazon_seller=is_amazon,
            is_fba=is_fba,
            fulfilled_by=product_response.fulfilled_by,
            # Amazon's Choice
            amazons_choice_keywords=product_response.amazons_choice_keywords
            if product_response.amazons_choice_keywords
            else None,
            has_amazons_choice=has_amazons_choice,
            # Variations
            has_variations=has_variations,
            variation_types=variation_types,
            total_variations=total_variations,
            dimensions_map=product_response.dimensions if product_response.dimensions else None,
            variation_values=product_response.variation_values
            if product_response.variation_values
            else None,
            # Additional
            coupon_text=None,  # Not in new response
            deal_type="deal" if product_response.deal else None,
            is_deal=product_response.deal,
            prime=product_response.prime,
            is_prime=product_response.prime,
            is_used=product_response.used,
            past_sales=product_response.past_sales,
            delivery_message=product_response.delivery_message,
            product_type=product_response.type,
            input_url=product_response.input_url,
        )
