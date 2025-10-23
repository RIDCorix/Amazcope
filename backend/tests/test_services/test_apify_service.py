"""Tests for ApifyService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from schemas.apify_schemas import ApifyProductResponse, BestSellerRank
from services.apify_service import ApifyService


class TestApifyServiceInit:
    """Test ApifyService initialization."""

    def test_init_with_valid_token(self):
        """Test initialization with valid API token."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token-123"

            service = ApifyService()

            assert service.client is not None
            assert service.PRODUCT_SCRAPER == "axesso_data/amazon-product-details-scraper"
            assert service.REVIEW_SCRAPER == "axesso_data/amazon-reviews-scraper"
            assert service.BESTSELLER_SCRAPER == "junglee/amazon-bestsellers"

    def test_init_without_token_raises_error(self):
        """Test initialization fails without API token."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = None

            with pytest.raises(ValueError, match="APIFY_API_TOKEN not configured"):
                ApifyService()


class TestExtractASINFromURL:
    """Test ASIN extraction from URLs."""

    def test_extract_asin_standard_dp_format(self):
        """Test ASIN extraction from standard /dp/ URL."""
        url = "https://www.amazon.com/dp/B01ABCD123"

        asin = ApifyService.extract_asin_from_url(url)

        assert asin == "B01ABCD123"

    def test_extract_asin_with_product_name(self):
        """Test ASIN extraction from URL with product name."""
        url = "https://www.amazon.com/Product-Name-Here/dp/B01ABCD123/ref=sr_1_1"

        asin = ApifyService.extract_asin_from_url(url)

        assert asin == "B01ABCD123"

    def test_extract_asin_gp_product_format(self):
        """Test ASIN extraction from /gp/product/ URL."""
        url = "https://www.amazon.com/gp/product/B01ABCD123"

        asin = ApifyService.extract_asin_from_url(url)

        assert asin == "B01ABCD123"

    def test_extract_asin_from_query_param(self):
        """Test ASIN extraction from query parameter."""
        url = "https://www.amazon.com/s?asin=B01ABCD123"

        asin = ApifyService.extract_asin_from_url(url)

        assert asin == "B01ABCD123"

    def test_extract_asin_lowercase_converted_to_uppercase(self):
        """Test lowercase ASIN is converted to uppercase."""
        url = "https://www.amazon.com/dp/b01abcd123"

        asin = ApifyService.extract_asin_from_url(url)

        assert asin == "B01ABCD123"

    def test_extract_asin_invalid_url_returns_none(self):
        """Test invalid URL returns None."""
        url = "https://www.example.com/no-asin-here"

        asin = ApifyService.extract_asin_from_url(url)

        assert asin is None

    def test_extract_asin_invalid_length_returns_none(self):
        """Test ASIN with invalid length returns None."""
        url = "https://www.amazon.com/dp/B01ABC"  # Only 6 chars

        asin = ApifyService.extract_asin_from_url(url)

        assert asin is None


class TestExtractMarketplaceFromURL:
    """Test marketplace extraction from URLs."""

    def test_extract_marketplace_com(self):
        """Test extracting .com marketplace."""
        url = "https://www.amazon.com/dp/B01ABCD123"

        marketplace = ApifyService.extract_marketplace_from_url(url)

        assert marketplace == "com"

    def test_extract_marketplace_uk(self):
        """Test extracting .co.uk marketplace."""
        url = "https://www.amazon.co.uk/dp/B01ABCD123"

        marketplace = ApifyService.extract_marketplace_from_url(url)

        assert marketplace == "co.uk"

    def test_extract_marketplace_de(self):
        """Test extracting .de marketplace."""
        url = "https://www.amazon.de/dp/B01ABCD123"

        marketplace = ApifyService.extract_marketplace_from_url(url)

        assert marketplace == "de"

    def test_extract_marketplace_japan(self):
        """Test extracting .co.jp marketplace."""
        url = "https://www.amazon.co.jp/dp/B01ABCD123"

        marketplace = ApifyService.extract_marketplace_from_url(url)

        assert marketplace == "co.jp"

    def test_extract_marketplace_invalid_defaults_to_com(self):
        """Test invalid marketplace defaults to com."""
        url = "https://www.amazon.invalid/dp/B01ABCD123"

        marketplace = ApifyService.extract_marketplace_from_url(url)

        assert marketplace == "com"


class TestASINToURL:
    """Test ASIN to URL conversion."""

    def test_asin_to_url_default_domain(self):
        """Test ASIN to URL with default domain."""
        asin = "B01ABCD123"

        url = ApifyService._asin_to_url(asin)

        assert url == "https://www.amazon.com/dp/B01ABCD123"

    def test_asin_to_url_custom_domain(self):
        """Test ASIN to URL with custom domain."""
        asin = "B01ABCD123"

        url = ApifyService._asin_to_url(asin, domain="amazon.de")

        assert url == "https://www.amazon.de/dp/B01ABCD123"


class TestScrapeProduct:
    """Test single product scraping."""

    @pytest.mark.asyncio
    async def test_scrape_product_success(self):
        """Test successful product scraping."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            # Mock scrape_products_batch to return test data
            mock_result = MagicMock()
            mock_result.asin = "B01ABCD123"
            mock_result.title = "Test Product"

            with patch.object(
                service, "scrape_products_batch", new_callable=AsyncMock
            ) as mock_batch:
                mock_batch.return_value = {"B01ABCD123": mock_result}

                result = await service.scrape_product("B01ABCD123")

                assert result == mock_result
                mock_batch.assert_called_once_with(["B01ABCD123"], marketplace="com")

    @pytest.mark.asyncio
    async def test_scrape_product_custom_marketplace(self):
        """Test product scraping with custom marketplace."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            with patch.object(
                service, "scrape_products_batch", new_callable=AsyncMock
            ) as mock_batch:
                mock_batch.return_value = {"B01ABCD123": MagicMock()}

                await service.scrape_product("B01ABCD123", marketplace="de")

                mock_batch.assert_called_once_with(["B01ABCD123"], marketplace="de")

    @pytest.mark.asyncio
    async def test_scrape_product_no_results_raises_error(self):
        """Test scraping raises error when no results returned."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            with patch.object(
                service, "scrape_products_batch", new_callable=AsyncMock
            ) as mock_batch:
                mock_batch.return_value = {}

                with pytest.raises(ValueError, match="No results returned for ASIN"):
                    await service.scrape_product("B01ABCD123")


class TestScrapeProductsBatch:
    """Test batch product scraping."""

    @pytest.mark.asyncio
    async def test_scrape_products_batch_single_product(self):
        """Test batch scraping with single product."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            # Mock Apify client
            mock_run = {"defaultDatasetId": "dataset-123"}
            mock_actor = MagicMock()
            mock_actor.call = AsyncMock(return_value=mock_run)
            service.client.actor = MagicMock(return_value=mock_actor)

            # Mock dataset iterator
            mock_item = {
                "asin": "B01ABCD123",
                "title": "Test Product",
                "price": 29.99,
                "url": "https://www.amazon.com/dp/B01ABCD123",
                "statusCode": 200,
                "statusMessage": "OK",
            }

            async def mock_iterator():
                yield mock_item

            mock_dataset = MagicMock()
            mock_dataset.iterate_items = mock_iterator
            service.client.dataset = MagicMock(return_value=mock_dataset)

            # Mock _normalize_product_data
            mock_normalized = MagicMock()
            with patch.object(service, "_normalize_product_data", return_value=mock_normalized):
                results = await service.scrape_products_batch(["B01ABCD123"])

                assert len(results) == 1
                assert "B01ABCD123" in results
                assert results["B01ABCD123"] == mock_normalized

    @pytest.mark.asyncio
    async def test_scrape_products_batch_handles_404(self):
        """Test batch scraping handles 404 status."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            # Mock Apify client
            mock_run = {"defaultDatasetId": "dataset-123"}
            mock_actor = MagicMock()
            mock_actor.call = AsyncMock(return_value=mock_run)
            service.client.actor = MagicMock(return_value=mock_actor)

            # Mock 404 response
            mock_item = {
                "asin": "B01ABCD123",
                "title": "Not Found",
                "url": "https://www.amazon.com/dp/B01ABCD123",
                "statusCode": 404,
                "statusMessage": "Not Found",
            }

            async def mock_iterator():
                yield mock_item

            mock_dataset = MagicMock()
            mock_dataset.iterate_items = mock_iterator
            service.client.dataset = MagicMock(return_value=mock_dataset)

            results = await service.scrape_products_batch(["B01ABCD123"])

            assert len(results) == 1
            assert results["B01ABCD123"] == {"status": "404", "asin": "B01ABCD123"}

    @pytest.mark.asyncio
    async def test_scrape_products_batch_large_batch(self):
        """Test batch scraping handles batches over 100 items."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            # Mock Apify client for 2 batches
            mock_run = {"defaultDatasetId": "dataset-123"}
            mock_actor = MagicMock()
            mock_actor.call = AsyncMock(return_value=mock_run)
            service.client.actor = MagicMock(return_value=mock_actor)

            # Create 150 ASINs (should split into 2 batches)
            asins = [f"B0{i:08d}" for i in range(150)]

            # Mock empty dataset (just verify batching logic)
            async def mock_iterator():
                return
                yield  # Make it an async generator

            mock_dataset = MagicMock()
            mock_dataset.iterate_items = mock_iterator
            service.client.dataset = MagicMock(return_value=mock_dataset)

            await service.scrape_products_batch(asins)

            # Verify actor was called twice (2 batches of 100 and 50)
            assert mock_actor.call.call_count == 2


class TestScrapeReviews:
    """Test review scraping."""

    @pytest.mark.asyncio
    async def test_scrape_reviews_success(self):
        """Test successful review scraping."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            # Mock Apify client
            mock_run = {"defaultDatasetId": "dataset-123"}
            mock_actor = MagicMock()
            mock_actor.call = AsyncMock(return_value=mock_run)
            service.client.actor = MagicMock(return_value=mock_actor)

            # Mock review data
            mock_review = {
                "reviewId": "R123",
                "title": "Great product!",
                "text": "Love it",
                "stars": 5,
                "verifiedPurchase": True,
                "date": "January 1, 2024",
            }

            async def mock_iterator():
                yield mock_review

            mock_dataset = MagicMock()
            mock_dataset.iterate_items = mock_iterator
            service.client.dataset = MagicMock(return_value=mock_dataset)

            url = "https://www.amazon.com/dp/B01ABCD123"
            reviews = await service.scrape_reviews(url, max_reviews=50)

            assert len(reviews) == 1
            assert reviews[0]["review_id"] == "R123"
            assert reviews[0]["title"] == "Great product!"
            assert reviews[0]["rating"] == 5.0

    @pytest.mark.asyncio
    async def test_scrape_reviews_with_custom_params(self):
        """Test review scraping with custom parameters."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            mock_run = {"defaultDatasetId": "dataset-123"}
            mock_actor = MagicMock()
            mock_actor.call = AsyncMock(return_value=mock_run)
            service.client.actor = MagicMock(return_value=mock_actor)

            async def mock_iterator():
                return
                yield

            mock_dataset = MagicMock()
            mock_dataset.iterate_items = mock_iterator
            service.client.dataset = MagicMock(return_value=mock_dataset)

            url = "https://www.amazon.com/dp/B01ABCD123"
            await service.scrape_reviews(url, max_reviews=200, sort_by="helpful")

            # Verify actor was called with correct params
            call_args = mock_actor.call.call_args
            assert call_args[1]["run_input"]["maxReviews"] == 200
            assert call_args[1]["run_input"]["sortBy"] == "helpful"

    @pytest.mark.asyncio
    async def test_scrape_reviews_error_returns_empty_list(self):
        """Test review scraping returns empty list on error."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            # Mock actor to raise exception
            mock_actor = MagicMock()
            mock_actor.call = AsyncMock(side_effect=Exception("API Error"))
            service.client.actor = MagicMock(return_value=mock_actor)

            url = "https://www.amazon.com/dp/B01ABCD123"
            reviews = await service.scrape_reviews(url)

            assert reviews == []


class TestScrapeBestsellers:
    """Test bestseller scraping."""

    @pytest.mark.asyncio
    async def test_scrape_bestsellers_success(self):
        """Test successful bestseller scraping."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            # Mock Apify client
            mock_run = {"defaultDatasetId": "dataset-123"}
            mock_actor = MagicMock()
            mock_actor.call = AsyncMock(return_value=mock_run)
            service.client.actor = MagicMock(return_value=mock_actor)

            # Mock bestseller data
            mock_item = {
                "position": 1,
                "asin": "B01ABCD123",
                "title": "Bestseller Product",
                "price": {"value": 29.99},
            }

            async def mock_iterator():
                yield mock_item

            mock_dataset = MagicMock()
            mock_dataset.iterate_items = mock_iterator
            service.client.dataset = MagicMock(return_value=mock_dataset)

            url = "https://www.amazon.com/best-sellers-electronics"
            items = await service.scrape_bestsellers(url)

            assert len(items) == 1
            assert items[0]["asin"] == "B01ABCD123"

    @pytest.mark.asyncio
    async def test_scrape_bestsellers_no_results_raises_error(self):
        """Test bestseller scraping raises error when no results."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"

            service = ApifyService()

            mock_run = {"defaultDatasetId": "dataset-123"}
            mock_actor = MagicMock()
            mock_actor.call = AsyncMock(return_value=mock_run)
            service.client.actor = MagicMock(return_value=mock_actor)

            # Mock empty dataset
            async def mock_iterator():
                return
                yield

            mock_dataset = MagicMock()
            mock_dataset.iterate_items = mock_iterator
            service.client.dataset = MagicMock(return_value=mock_dataset)

            url = "https://www.amazon.com/best-sellers-electronics"

            with pytest.raises(ValueError, match="No bestsellers data returned"):
                await service.scrape_bestsellers(url)


class TestNormalizeReviewData:
    """Test review data normalization."""

    def test_normalize_review_data_complete(self):
        """Test normalizing complete review data."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"
            service = ApifyService()

            raw_data = {
                "reviewId": "R123456",
                "title": "Excellent product",
                "text": "This is a great product",
                "stars": 5,
                "verifiedPurchase": True,
                "helpful": 10,
                "date": "January 15, 2024",
                "name": "John Doe",
                "reviewerId": "USER123",
                "isVine": False,
                "images": ["image1.jpg"],
                "variant": "Color: Black",
            }

            normalized = service._normalize_review_data(raw_data)

            assert normalized["review_id"] == "R123456"
            assert normalized["title"] == "Excellent product"
            assert normalized["rating"] == 5.0
            assert normalized["verified_purchase"] is True
            assert normalized["helpful_count"] == 10
            assert normalized["reviewer_name"] == "John Doe"

    def test_normalize_review_data_minimal(self):
        """Test normalizing minimal review data."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"
            service = ApifyService()

            raw_data = {
                "id": "R123",
                "rating": 3,
            }

            normalized = service._normalize_review_data(raw_data)

            assert normalized["review_id"] == "R123"
            assert normalized["rating"] == 3.0
            assert normalized["title"] == ""
            assert normalized["verified_purchase"] is False


class TestNormalizeProductData:
    """Test product data normalization."""

    def test_normalize_product_data_complete(self):
        """Test normalizing complete product data."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"
            service = ApifyService()

            # Create mock ApifyProductResponse
            product_response = ApifyProductResponse(
                status_code=200,
                status_message="OK",
                asin="B01ABCD123",
                title="Test Product",
                url="https://www.amazon.com/dp/B01ABCD123",
                price=29.99,
                retail_price=39.99,
                manufacturer="Test Brand",
                product_rating="4.5 out of 5 stars",
                count_review=100,
                warehouse_availability="In Stock",
                best_sellers_rank=[
                    BestSellerRank(
                        rank="1,234",
                        category_name="Electronics",
                        link="https://amazon.com/bestsellers/electronics",
                    )
                ],
                image_url_list=["image1.jpg"],
                features=["Feature 1", "Feature 2"],
                product_description="Great product",
            )

            normalized = service._normalize_product_data(product_response)

            assert normalized.asin == "B01ABCD123"
            assert normalized.title == "Test Product"
            assert normalized.price == 29.99
            assert normalized.original_price == 39.99
            assert normalized.rating == 4.5
            assert normalized.bsr_main_category == 1234

    def test_normalize_product_data_with_404_status(self):
        """Test normalizing product with 404 status is handled upstream."""
        with patch("services.apify_service.settings") as mock_settings:
            mock_settings.APIFY_API_TOKEN = "test-token"
            service = ApifyService()

            # 404 products are handled in scrape_products_batch, not in normalize
            # This test verifies the normalize function handles minimal data
            product_response = ApifyProductResponse(
                status_code=404,
                status_message="Not Found",
                asin="B01ABCD123",
                title="Not Found",
                url="https://www.amazon.com/dp/B01ABCD123",
            )

            normalized = service._normalize_product_data(product_response)

            assert normalized.asin == "B01ABCD123"
            assert normalized.price is None
            assert normalized.bsr_main_category is None
