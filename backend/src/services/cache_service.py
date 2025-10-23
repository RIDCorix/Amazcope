"""Redis cache service for storing frequently accessed data."""

import json
import logging
from typing import Any, cast

import redis.asyncio as redis

from core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for interacting with Redis cache.

    Provides methods for:
    - Caching product snapshots (24-48 hours)
    - Caching product summaries
    - Rate limiting keys
    - Session storage
    """

    def __init__(self) -> None:
        """Initialize Redis client."""
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 1 hour)

        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return cast(bool, await self.redis.exists(key) > 0)
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {str(e)}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter key.

        Args:
            key: Counter key
            amount: Amount to increment by

        Returns:
            New counter value
        """
        try:
            return cast(int, await self.redis.incrby(key, amount))
        except Exception as e:
            logger.error(f"Error incrementing cache key {key}: {str(e)}")
            return 0

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple keys at once.

        Args:
            keys: List of cache keys

        Returns:
            Dict mapping keys to values
        """
        try:
            values = await self.redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"Error getting multiple cache keys: {str(e)}")
            return {}

    async def set_many(self, items: dict[str, Any], ttl: int = 3600) -> bool:
        """Set multiple keys at once.

        Args:
            items: Dict mapping keys to values
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            pipeline = self.redis.pipeline()
            for key, value in items.items():
                serialized = json.dumps(value, default=str)
                pipeline.setex(key, ttl, serialized)
            await pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"Error setting multiple cache keys: {str(e)}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "product:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return cast(int, await self.redis.delete(*keys))
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {str(e)}")
            return 0

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()
