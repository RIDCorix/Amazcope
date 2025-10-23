import time

from pydantic_settings import BaseSettings

from system.checks import BaseCheck, CheckResult
from system.registries import dependency_registry


class DramatiqSettings(BaseSettings):
    """Dramatiq worker settings."""


@dependency_registry.register()
class DramatiqTest(BaseCheck):
    """Test Dramatiq broker connectivity."""

    name = "dramatiq"

    async def test(self) -> CheckResult:
        """Test Dramatiq broker connection."""
        from core.config import settings
        from system.tasks import simple_add

        start_time = time.time()
        # Send a test task (Dramatiq is fire-and-forget by default)
        message = simple_add.send(x=1, y=2)
        result = message.get_result(block=True, timeout=10 * 1000)
        assert result == 3, "Dramatiq task did not return expected result"
        duration_ms = (time.time() - start_time) * 1000

        return CheckResult(
            name=self.name,
            status="success",
            message="Dramatiq broker connection successful",
            details={
                "broker_url": settings.REDIS_URL,
                "worker_processes": 2,
                "worker_threads": 4,
            },
            duration_ms=duration_ms,
        )
