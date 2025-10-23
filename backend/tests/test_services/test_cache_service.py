"""Tests for CacheService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.cache_service import CacheService


class TestCacheServiceInit:
    """Test CacheService initialization."""

    @patch("services.cache_service.redis.from_url")
    def test_cache_service_initialization(self, mock_redis):
        """Test service initializes Redis client."""
        mock_redis.return_value = MagicMock()

        service = CacheService()

        assert service.redis is not None
        mock_redis.assert_called_once()


class TestCacheGet:
    """Test cache get operations."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_get_existing_key(self, mock_redis):
        """Test getting an existing cache key."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value='{"name": "test", "value": 42}')
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.get("test:key")

        assert result == {"name": "test", "value": 42}
        mock_client.get.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_get_nonexistent_key(self, mock_redis):
        """Test getting a non-existent cache key."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.get("missing:key")

        assert result is None

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_get_error_handling(self, mock_redis):
        """Test get handles Redis errors gracefully."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Redis connection failed"))
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.get("error:key")

        assert result is None


class TestCacheSet:
    """Test cache set operations."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_set_value_success(self, mock_redis):
        """Test setting a cache value successfully."""
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock(return_value=True)
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.set("test:key", {"data": "value"}, ttl=3600)

        assert result is True
        mock_client.setex.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_set_with_custom_ttl(self, mock_redis):
        """Test setting value with custom TTL."""
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock(return_value=True)
        mock_redis.return_value = mock_client

        service = CacheService()
        await service.set("test:key", {"data": "value"}, ttl=7200)

        # Verify TTL was passed correctly
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 7200  # TTL argument

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_set_error_handling(self, mock_redis):
        """Test set handles errors gracefully."""
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock(side_effect=Exception("Write failed"))
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.set("error:key", {"data": "value"})

        assert result is False


class TestCacheDelete:
    """Test cache delete operations."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_delete_key_success(self, mock_redis):
        """Test deleting a cache key successfully."""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=1)
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.delete("test:key")

        assert result is True
        mock_client.delete.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_delete_error_handling(self, mock_redis):
        """Test delete handles errors gracefully."""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(side_effect=Exception("Delete failed"))
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.delete("error:key")

        assert result is False


class TestCacheExists:
    """Test cache exists operations."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_exists_key_present(self, mock_redis):
        """Test checking existence of present key."""
        mock_client = AsyncMock()
        mock_client.exists = AsyncMock(return_value=1)
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.exists("test:key")

        assert result is True

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_exists_key_absent(self, mock_redis):
        """Test checking existence of absent key."""
        mock_client = AsyncMock()
        mock_client.exists = AsyncMock(return_value=0)
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.exists("missing:key")

        assert result is False


class TestCacheIncrement:
    """Test cache increment operations."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_increment_counter(self, mock_redis):
        """Test incrementing a counter."""
        mock_client = AsyncMock()
        mock_client.incrby = AsyncMock(return_value=5)
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.increment("counter:key", amount=1)

        assert result == 5
        mock_client.incrby.assert_called_once_with("counter:key", 1)

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_increment_by_custom_amount(self, mock_redis):
        """Test incrementing by custom amount."""
        mock_client = AsyncMock()
        mock_client.incrby = AsyncMock(return_value=15)
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.increment("counter:key", amount=10)

        assert result == 15


class TestCacheGetMany:
    """Test getting multiple cache keys."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_get_many_keys(self, mock_redis):
        """Test getting multiple keys at once."""
        mock_client = AsyncMock()
        mock_client.mget = AsyncMock(
            return_value=[
                '{"id": 1, "name": "Product 1"}',
                '{"id": 2, "name": "Product 2"}',
                None,  # Missing key
            ]
        )
        mock_redis.return_value = mock_client

        service = CacheService()
        keys = ["product:1", "product:2", "product:3"]
        result = await service.get_many(keys)

        assert len(result) == 2
        assert result["product:1"]["id"] == 1
        assert result["product:2"]["id"] == 2
        assert "product:3" not in result

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_get_many_error_handling(self, mock_redis):
        """Test get_many handles errors gracefully."""
        mock_client = AsyncMock()
        mock_client.mget = AsyncMock(side_effect=Exception("Connection error"))
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.get_many(["key1", "key2"])

        assert result == {}


class TestCacheSetMany:
    """Test setting multiple cache keys."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_set_many_keys(self, mock_redis):
        """Test setting multiple keys at once."""
        mock_client = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock()
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)
        mock_redis.return_value = mock_client

        service = CacheService()
        items = {
            "product:1": {"id": 1, "name": "Product 1"},
            "product:2": {"id": 2, "name": "Product 2"},
        }
        result = await service.set_many(items, ttl=3600)

        assert result is True

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_set_many_error_handling(self, mock_redis):
        """Test set_many handles errors gracefully."""
        mock_client = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(side_effect=Exception("Pipeline error"))
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)
        mock_redis.return_value = mock_client

        service = CacheService()
        items = {"key1": "value1", "key2": "value2"}
        result = await service.set_many(items)

        assert result is False


class TestCacheClearPattern:
    """Test clearing cache keys by pattern."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_clear_pattern_success(self, mock_redis):
        """Test clearing keys matching pattern."""
        mock_client = AsyncMock()

        # Mock scan_iter to return keys
        async def mock_scan_iter(match):
            for key in ["product:1", "product:2", "product:3"]:
                yield key

        mock_client.scan_iter = mock_scan_iter
        mock_client.delete = AsyncMock(return_value=3)
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.clear_pattern("product:*")

        assert result == 3

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_clear_pattern_no_matches(self, mock_redis):
        """Test clearing pattern with no matching keys."""
        mock_client = AsyncMock()

        async def mock_scan_iter(match):
            return
            yield  # Make it a generator

        mock_client.scan_iter = mock_scan_iter
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.clear_pattern("nonexistent:*")

        assert result == 0


class TestCacheClose:
    """Test closing cache connection."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_close_connection(self, mock_redis):
        """Test closing Redis connection."""
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        mock_redis.return_value = mock_client

        service = CacheService()
        await service.close()

        mock_client.close.assert_called_once()


class TestCacheIntegration:
    """Integration tests for cache operations."""

    @pytest.mark.asyncio
    @patch("services.cache_service.redis.from_url")
    async def test_set_get_delete_flow(self, mock_redis):
        """Test complete set -> get -> delete flow."""
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock(return_value=True)
        mock_client.get = AsyncMock(return_value='{"data": "test"}')
        mock_client.delete = AsyncMock(return_value=1)
        mock_redis.return_value = mock_client

        service = CacheService()

        # Set value
        set_result = await service.set("test:key", {"data": "test"})
        assert set_result is True

        # Get value
        get_result = await service.get("test:key")
        assert get_result == {"data": "test"}

        # Delete value
        delete_result = await service.delete("test:key")
        assert delete_result is True
