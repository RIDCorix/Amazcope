"""Tests for utility modules."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.ai_tools import generate_tool_spec, get_openai_client, get_system_prompt
from utils.db_helpers import (
    batch_update_product_timestamps,
    get_active_products,
    get_all_active_users,
    get_products_by_ids,
    get_recent_snapshots,
    get_user_product_count,
)


class TestDBHelpers:
    """Test database helper utilities."""

    @pytest.mark.asyncio
    @patch("utils.db_helpers.get_async_db_context")
    async def test_get_active_products(self, mock_db_context):
        """Test getting active products."""
        # Mock database context and query results
        mock_db = AsyncMock()
        mock_db_context.return_value.__aenter__.return_value = mock_db

        # Create mock result chain
        mock_scalars_result = MagicMock()
        mock_scalars_result.all.return_value = [
            MagicMock(id=1, title="Product 1"),
            MagicMock(id=2, title="Product 2"),
        ]

        # Mock result that has synchronous scalars() method
        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars_result

        # Make execute() return the mock result
        mock_db.execute = AsyncMock(return_value=mock_execute_result)

        products = await get_active_products(limit=10)

        assert len(products) == 2
        assert mock_db.execute.called

    @pytest.mark.asyncio
    @patch("utils.db_helpers.get_async_db_context")
    async def test_get_active_products_with_user_filter(self, mock_db_context):
        """Test getting active products filtered by user."""
        mock_db = AsyncMock()
        mock_db_context.return_value.__aenter__.return_value = mock_db

        # Create mock result chain
        mock_scalars_result = MagicMock()
        mock_scalars_result.all.return_value = [
            MagicMock(id=1, created_by_id=1),
        ]

        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars_result
        mock_db.execute = AsyncMock(return_value=mock_execute_result)

        products = await get_active_products(user_id=1)

        assert len(products) == 1
        assert products[0].created_by_id == 1

    @pytest.mark.asyncio
    @patch("utils.db_helpers.get_async_db_context")
    async def test_get_all_active_users(self, mock_db_context):
        """Test getting all active users."""
        mock_db = AsyncMock()
        mock_db_context.return_value.__aenter__.return_value = mock_db

        # Create mock result chain
        mock_scalars_result = MagicMock()
        mock_scalars_result.all.return_value = [
            MagicMock(id=1, email="user1@example.com"),
            MagicMock(id=2, email="user2@example.com"),
        ]

        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars_result
        mock_db.execute = AsyncMock(return_value=mock_execute_result)

        users = await get_all_active_users()

        assert len(users) == 2
        assert users[0].email == "user1@example.com"

    @pytest.mark.asyncio
    @patch("utils.db_helpers.get_async_db_context")
    async def test_get_recent_snapshots(self, mock_db_context):
        """Test getting recent snapshots for a product."""
        mock_db = AsyncMock()
        mock_db_context.return_value.__aenter__.return_value = mock_db

        # Create mock result chain
        mock_scalars_result = MagicMock()
        mock_scalars_result.all.return_value = [
            MagicMock(id=1, price=29.99),
            MagicMock(id=2, price=30.99),
        ]

        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars_result
        mock_db.execute = AsyncMock(return_value=mock_execute_result)

        snapshots = await get_recent_snapshots(product_id=1, limit=10)

        assert len(snapshots) == 2
        assert snapshots[0].price == 29.99

    @pytest.mark.asyncio
    @patch("utils.db_helpers.get_async_db_context")
    async def test_get_products_by_ids(self, mock_db_context):
        """Test getting products by IDs."""
        mock_db = AsyncMock()
        mock_db_context.return_value.__aenter__.return_value = mock_db

        # Create mock result chain
        mock_scalars_result = MagicMock()
        mock_scalars_result.all.return_value = [
            MagicMock(id=1, title="Product 1"),
            MagicMock(id=2, title="Product 2"),
        ]

        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars_result
        mock_db.execute = AsyncMock(return_value=mock_execute_result)

        products = await get_products_by_ids([1, 2])

        assert len(products) == 2
        assert products[0].id == 1

    @pytest.mark.asyncio
    async def test_get_products_by_ids_empty_list(self):
        """Test getting products with empty ID list."""
        products = await get_products_by_ids([])
        assert products == []

    @pytest.mark.asyncio
    @patch("utils.db_helpers.get_async_db_context")
    async def test_batch_update_product_timestamps(self, mock_db_context):
        """Test batch updating product timestamps."""
        mock_db = AsyncMock()
        mock_db_context.return_value.__aenter__.return_value = mock_db

        await batch_update_product_timestamps([1, 2, 3])

        assert mock_db.execute.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_batch_update_product_timestamps_empty_list(self):
        """Test batch update with empty list."""
        # Should not raise error
        await batch_update_product_timestamps([])

    @pytest.mark.asyncio
    @patch("utils.db_helpers.get_async_db_context")
    async def test_get_user_product_count(self, mock_db_context):
        """Test getting user product count."""
        mock_db = AsyncMock()
        mock_db_context.return_value.__aenter__.return_value = mock_db

        # Create mock result chain
        mock_scalars_result = MagicMock()
        mock_scalars_result.all.return_value = [1, 2, 3]

        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars_result
        mock_db.execute = AsyncMock(return_value=mock_execute_result)

        count = await get_user_product_count(user_id=1)

        assert count == 3


class TestAITools:
    """Test AI tool utilities."""

    def test_generate_tool_spec_basic_function(self):
        """Test generating tool spec for basic function."""

        def sample_function(param1: str, param2: int) -> str:
            """Sample function for testing.

            Args:
                param1: First parameter description
                param2: Second parameter description

            Returns:
                Result string
            """
            return f"{param1}-{param2}"

        spec = generate_tool_spec(sample_function)

        assert spec["type"] == "function"
        assert spec["function"]["name"] == "sample_function"
        assert "param1" in spec["function"]["parameters"]["properties"]
        assert "param2" in spec["function"]["parameters"]["properties"]

    def test_generate_tool_spec_parameter_types(self):
        """Test tool spec generation with different parameter types."""

        def multi_type_function(
            string_param: str, int_param: int, float_param: float, bool_param: bool
        ) -> None:
            """Multi-type function."""
            pass

        spec = generate_tool_spec(multi_type_function)
        properties = spec["function"]["parameters"]["properties"]

        assert properties["string_param"]["type"] == "string"
        assert properties["int_param"]["type"] == "integer"
        assert properties["float_param"]["type"] == "number"
        assert properties["bool_param"]["type"] == "boolean"

    def test_generate_tool_spec_optional_parameters(self):
        """Test tool spec with optional parameters."""

        def optional_function(required: str, optional: str = "default") -> None:
            """Function with optional parameter."""
            pass

        spec = generate_tool_spec(optional_function)
        required_params = spec["function"]["parameters"]["required"]
        properties = spec["function"]["parameters"]["properties"]

        assert "required" in required_params
        assert "optional" not in required_params
        assert properties["optional"]["default"] == "default"

    def test_generate_tool_spec_with_docstring(self):
        """Test tool spec generation includes docstring."""

        def documented_function(param: str) -> str:
            """This is a well-documented function.

            Args:
                param: Parameter description

            Returns:
                Result description
            """
            return param

        spec = generate_tool_spec(documented_function)

        assert "well-documented" in spec["function"]["description"]

    def test_get_system_prompt(self):
        """Test getting system prompt."""
        prompt = get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Amazon" in prompt
        assert "optimization" in prompt

    def test_get_system_prompt_content(self):
        """Test system prompt contains required sections."""
        prompt = get_system_prompt()

        assert "ANALYSIS WORKFLOW" in prompt
        assert "WHAT TO LOOK FOR" in prompt
        assert "SUGGESTION PRIORITIES" in prompt
        assert "DAILY REPORT REQUIREMENTS" in prompt

    @patch("utils.ai_tools.openai.AsyncOpenAI")
    def test_get_openai_client(self, mock_openai):
        """Test getting OpenAI client."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        client = get_openai_client()

        assert mock_openai.called
        assert client == mock_client
