import time

from pydantic_settings import BaseSettings

from system.checks import BaseCheck, CheckResult
from system.registries import dependency_registry


class CacheSettings(BaseSettings):
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_HOST: str = "localhost"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@dependency_registry.register()
class RedisTest(BaseCheck):
    """Test Redis connectivity."""

    name = "redis"

    async def test(self) -> CheckResult:
        """Test Redis connection."""
        from core.config import settings
        from core.redis import redis_client

        start_time = time.time()

        # Test basic connection
        redis_client.ping()

        # Test read/write operations
        test_key = "health_check_test"
        test_value = "test_value_123"

        await redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = await redis_client.get(test_key)
        await redis_client.delete(test_key)

        duration_ms = (time.time() - start_time) * 1000

        if retrieved_value == test_value:
            return CheckResult(
                name=self.name,
                status="success",
                message="Redis connection and operations successful",
                details={
                    "host": settings.REDIS_HOST,
                    "port": settings.REDIS_PORT,
                    "db": settings.REDIS_DB,
                    "read_write_test": "passed",
                },
                duration_ms=duration_ms,
            )
        else:
            return CheckResult(
                name=self.name,
                status="warning",
                message="Redis connected but read/write test failed",
                details={
                    "host": settings.REDIS_HOST,
                    "port": settings.REDIS_PORT,
                    "db": settings.REDIS_DB,
                    "expected": test_value,
                    "got": retrieved_value,
                },
                duration_ms=duration_ms,
            )
