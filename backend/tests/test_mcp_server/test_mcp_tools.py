"""Tests for MCP Server Tools.

Tests the MCP (Model Context Protocol) tools that AI agents use to
interact with the Amazcope product tracking system.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import mcp_server.tools as mcp_tools
from optimization.models import Suggestion
from products.models import Product, ProductSnapshot
from users.models import User


class TestGetProductDetails:
    """Test get_product_details MCP tool."""

    @pytest.mark.asyncio
    async def test_get_product_details_success(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test getting product details successfully."""
        # Create a snapshot
        snapshot = ProductSnapshot(
            product_id=test_product.id,
            price=Decimal("29.99"),
            currency="USD",
            bsr_main_category=1000,
            rating=Decimal("4.5"),
            scraped_at=datetime.utcnow(),
        )
        db_session.add(snapshot)
        await db_session.commit()

        # Mock the context manager
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.get_product_details.fn(test_product.id)

            assert "error" not in result
            assert result["id"] == test_product.id
            assert result["asin"] == test_product.asin
            assert result["title"] == test_product.title
            assert result["current_price"] == 29.99
            assert result["currency"] == "USD"
            assert result["current_bsr"] == 1000

    @pytest.mark.asyncio
    async def test_get_product_details_not_found(self, db_session: AsyncSession):
        """Test getting details for non-existent product."""
        fake_id = uuid4()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.get_product_details.fn(fake_id)

            assert "error" in result
            assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_product_details_no_snapshot(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test getting product details when no snapshot exists."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.get_product_details.fn(test_product.id)

            assert "error" not in result
            assert result["current_price"] is None
            assert result["current_bsr"] is None


class TestSearchProducts:
    """Test search_products MCP tool."""

    @pytest.mark.asyncio
    async def test_search_products_by_title(self, db_session: AsyncSession, test_product: Product):
        """Test searching products by title."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.search_products.fn(query="Test")

            assert isinstance(result, list)
            assert len(result) > 0
            assert result[0]["asin"] == test_product.asin

    @pytest.mark.asyncio
    async def test_search_products_by_marketplace(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test searching products by marketplace."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.search_products.fn(marketplace="com")

            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_search_products_with_limit(self, db_session: AsyncSession):
        """Test search with custom limit."""
        # Create multiple products
        for i in range(15):
            product = Product(
                asin=f"B0{i:08d}",
                marketplace="com",
                title=f"Product {i}",
                url=f"https://www.amazon.com/dp/B0{i:08d}",
            )
            db_session.add(product)
        await db_session.commit()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.search_products.fn(limit=5)

            assert len(result) <= 5

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, db_session: AsyncSession):
        """Test search with no matching products."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.search_products.fn(query="NonexistentProduct12345")

            assert isinstance(result, list)
            assert len(result) == 0


class TestGetPriceHistory:
    """Test get_price_history MCP tool."""

    @pytest.mark.asyncio
    async def test_get_price_history_success(self, db_session: AsyncSession, test_product: Product):
        """Test getting price history."""
        # Create snapshots over 7 days
        for days_ago in range(7):
            snapshot = ProductSnapshot(
                product_id=test_product.id,
                price=Decimal(f"{30 + days_ago}.99"),
                scraped_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db_session.add(snapshot)
        await db_session.commit()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.get_price_history.fn(test_product.id, days=7)

            assert "error" not in result
            assert "history" in result
            assert len(result["history"]) > 0

    @pytest.mark.asyncio
    async def test_get_price_history_no_data(self, db_session: AsyncSession, test_product: Product):
        """Test getting price history with no snapshots."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.get_price_history.fn(test_product.id)

            assert "error" not in result
            assert result["history"] == []


class TestGetBSRHistory:
    """Test get_bsr_history MCP tool."""

    @pytest.mark.asyncio
    async def test_get_bsr_history_success(self, db_session: AsyncSession, test_product: Product):
        """Test getting BSR history."""
        # Create snapshots with BSR data
        for days_ago in range(7):
            snapshot = ProductSnapshot(
                product_id=test_product.id,
                bsr_main_category=1000 + (days_ago * 100),
                bsr_small_category=500 + (days_ago * 50),
                scraped_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db_session.add(snapshot)
        await db_session.commit()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.get_bsr_history.fn(test_product.id, days=7)

            assert "error" not in result
            assert "history" in result
            assert len(result["history"]) > 0


class TestGetCompetitorAnalysis:
    """Test get_competitor_analysis MCP tool."""

    @pytest.mark.asyncio
    async def test_get_competitor_analysis_success(
        self, db_session: AsyncSession, test_product: Product, test_user: User
    ):
        """Test getting competitor analysis."""
        # Create a competitor product
        competitor = Product(
            asin="B01COMPET1",
            marketplace="com",
            title="Competitor Product",
            url="https://www.amazon.com/dp/B01COMPET1",
            category=test_product.category,
        )
        db_session.add(competitor)
        await db_session.commit()
        await db_session.refresh(competitor)

        # Create snapshots for comparison
        for product in [test_product, competitor]:
            snapshot = ProductSnapshot(
                product_id=product.id,
                price=Decimal("29.99"),
                bsr_main_category=1000,
                rating=Decimal("4.5"),
                scraped_at=datetime.utcnow(),
            )
            db_session.add(snapshot)
        await db_session.commit()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.get_competitor_analysis.fn(test_product.id)

            assert "error" not in result
            assert "competitors" in result


class TestTriggerProductRefresh:
    """Test trigger_product_refresh MCP tool."""

    @pytest.mark.asyncio
    async def test_trigger_product_refresh_success(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test triggering product refresh."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            # Mock the scraping service
            with patch("scrapper.product_tracking_service.ProductTrackingService") as mock_service:
                mock_instance = MagicMock()
                mock_instance.refresh_product = AsyncMock(return_value=MagicMock())
                mock_service.return_value = mock_instance

                result = await mcp_tools.trigger_product_refresh.fn(str(test_product.id))

                assert "error" not in result or "message" in result


class TestGetUserProducts:
    """Test get_user_products MCP tool."""

    @pytest.mark.asyncio
    async def test_get_user_products_success(
        self, db_session: AsyncSession, test_user: User, test_product: Product
    ):
        """Test getting user's tracked products."""
        # Create user-product relationship
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.get_user_products.fn(test_user.id)

            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_user_products_empty(self, db_session: AsyncSession, test_user: User):
        """Test getting user products when user has none."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.get_user_products.fn(test_user.id)

            assert isinstance(result, list)
            assert len(result) == 0


class TestUpdateProductInfo:
    """Test update_product_info MCP tool."""

    @pytest.mark.asyncio
    async def test_update_product_info_success(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test updating product information."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.update_product_info.fn(
                product_id=test_product.id,
                title="Updated Title",
            )

            assert "error" not in result
            assert "message" in result

    @pytest.mark.asyncio
    async def test_update_product_info_not_found(self, db_session: AsyncSession):
        """Test updating non-existent product."""
        fake_id = uuid4()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.update_product_info.fn(product_id=fake_id, title="Test")

            assert "error" in result


class TestUpdateUserProductSettings:
    """Test update_user_product_settings MCP tool."""

    @pytest.mark.asyncio
    async def test_update_user_product_settings_success(
        self, db_session: AsyncSession, test_user: User, test_product: Product
    ):
        """Test updating user-product settings."""
        # Create user-product relationship

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.update_user_product_settings.fn(
                user_id=test_user.id,
                product_id=test_product.id,
                price_change_threshold=15.0,
                bsr_change_threshold=40.0,
                notes="Updated tracking notes",
            )
            assert "error" not in result
            assert "message" in result


class TestToggleProductTracking:
    """Test toggle_product_tracking MCP tool."""

    @pytest.mark.asyncio
    async def test_toggle_product_tracking_activate(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test activating product tracking."""
        test_product.is_active = False
        await db_session.commit()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.toggle_product_tracking.fn(test_product.id, is_active=True)

            assert "error" not in result
            assert "message" in result

    @pytest.mark.asyncio
    async def test_toggle_product_tracking_deactivate(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test deactivating product tracking."""
        test_product.is_active = True
        await db_session.commit()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.toggle_product_tracking.fn(test_product.id, is_active=False)

            assert "error" not in result


class TestUpdateAlertThresholds:
    """Test update_alert_thresholds MCP tool."""

    @pytest.mark.asyncio
    async def test_update_alert_thresholds_success(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test updating alert thresholds."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.update_alert_thresholds.fn(
                product_id=test_product.id,
                price_threshold=20.0,
                bsr_threshold=50.0,
            )

            assert "error" not in result
            assert "message" in result


class TestCreateSuggestion:
    """Test create_suggestion MCP tool."""

    @pytest.mark.asyncio
    async def test_create_suggestion_success(self, db_session: AsyncSession, test_product: Product):
        """Test creating a suggestion."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.create_suggestion.fn(
                product_id=test_product.id,
                category="pricing",
                priority="high",
                title="Price Optimization",
                description="Consider reducing price",
                reasoning="Competitor analysis shows...",
            )

            assert "error" not in result
            assert "suggestion_id" in result


class TestAddSuggestionAction:
    """Test add_suggestion_action MCP tool."""

    @pytest.mark.asyncio
    async def test_add_suggestion_action_success(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test adding an action to a suggestion."""
        # Create a suggestion first
        suggestion = Suggestion(
            product_id=test_product.id,
            category="pricing",
            priority="high",
            title="Test Suggestion",
            description="Test description",
            reasoning="Test reasoning",
            status="pending",
        )
        db_session.add(suggestion)
        await db_session.commit()
        await db_session.refresh(suggestion)

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.add_suggestion_action.fn(
                suggestion_id=suggestion.id,
                action_type="update_price",
                target_field="price",
                proposed_value="24.99",
                reasoning="Price optimization based on market analysis",
            )

            assert "error" not in result
            assert "action_id" in result


class TestProposePriceOptimization:
    """Test propose_price_optimization MCP tool."""

    @pytest.mark.asyncio
    async def test_propose_price_optimization_success(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test proposing price optimization."""
        # Create snapshot with price data
        snapshot = ProductSnapshot(
            product_id=test_product.id,
            price=Decimal("29.99"),
            bsr_main_category=1000,
            scraped_at=datetime.utcnow(),
        )
        db_session.add(snapshot)
        await db_session.commit()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.propose_price_optimization.fn(
                product_id=test_product.id,
                suggested_price=24.99,
                reasoning="Market analysis shows...",
            )

            assert "error" not in result or "suggestion_id" in result


class TestProposeContentImprovement:
    """Test propose_content_improvement MCP tool."""

    @pytest.mark.asyncio
    async def test_propose_content_improvement_success(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test proposing content improvement."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.propose_content_improvement.fn(
                product_id=test_product.id,
                field_to_improve="title",
                current_content="Old Title",
                improved_content="Improved SEO Title",
                reasoning="Better keywords for search visibility",
                expected_benefit="Increase in organic traffic",
            )

            assert "error" not in result or "suggestion_id" in result


class TestProposeTrackingAdjustment:
    """Test propose_tracking_adjustment MCP tool."""

    @pytest.mark.asyncio
    async def test_propose_tracking_adjustment_success(
        self, db_session: AsyncSession, test_product: Product
    ):
        """Test proposing tracking adjustment."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.propose_tracking_adjustment.fn(
                product_id=test_product.id,
                adjustment_type="price_threshold",
                new_value="15.0",
                reasoning="High volatility product needs tighter price monitoring",
            )

            assert "error" not in result or "suggestion_id" in result


class TestGenerateDailyReport:
    """Test generate_daily_report MCP tool."""

    @pytest.mark.asyncio
    async def test_generate_daily_report_success(
        self, db_session: AsyncSession, test_user: User, test_product: Product
    ):
        """Test generating daily report."""

        # Create snapshots for the report
        snapshot = ProductSnapshot(
            product_id=test_product.id,
            price=Decimal("29.99"),
            bsr_main_category=1000,
            rating=Decimal("4.5"),
            review_count=100,
            scraped_at=datetime.utcnow(),
        )
        db_session.add(snapshot)
        await db_session.commit()

        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.generate_daily_report.fn(
                user_id=str(test_user.id),
                products_analyzed=1,
                suggestions_created=1,
                critical_issues=0,
                opportunities=1,
                summary_message="Daily report generated successfully",
            )

            assert "error" not in result or "summary" in result

    @pytest.mark.asyncio
    async def test_generate_daily_report_no_products(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test generating report when user has no products."""
        with patch("mcp_server.tools.get_async_db_context") as mock_context:
            mock_context.return_value.__aenter__.return_value = db_session

            result = await mcp_tools.generate_daily_report.fn(
                user_id=str(test_user.id),
                products_analyzed=0,
                suggestions_created=0,
                critical_issues=0,
                opportunities=0,
                summary_message="No products found",
            )

            # Should handle gracefully
            assert isinstance(result, dict)
