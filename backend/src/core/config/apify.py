import time

import aiohttp
from pydantic_settings import BaseSettings

from system.checks import BaseCheck, CheckResult
from system.registries import dependency_registry


class ApifyConfig(BaseSettings):
    APIFY_API_TOKEN: str | None = None


@dependency_registry.register()
class ApifyTest(BaseCheck):
    """Test Apify service connectivity."""

    name = "apify"

    async def test(self) -> CheckResult:
        """Test Apify service connection."""
        from core.config import settings

        start_time = time.time()

        if not hasattr(settings, "APIFY_API_TOKEN") or not settings.APIFY_API_TOKEN:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name=self.name,
                status="warning",
                message="Apify API token not configured",
                details={"configured": False, "service": "Apify"},
                duration_ms=duration_ms,
            )

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {settings.APIFY_API_TOKEN}",
                "Content-Type": "application/json",
            }

            # Test API connectivity with a simple request
            async with session.get(
                "https://api.apify.com/v2/users/me",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                duration_ms = (time.time() - start_time) * 1000

                if response.status == 200:
                    user_data = await response.json()
                    return CheckResult(
                        name=self.name,
                        status="success",
                        message="Apify service connection successful",
                        details={
                            "status_code": response.status,
                            "user_id": user_data.get("data", {}).get("id", "unknown"),
                            "api_version": "v2",
                        },
                        duration_ms=duration_ms,
                    )
                else:
                    return CheckResult(
                        name=self.name,
                        status="error",
                        message=f"Apify service returned status {response.status}",
                        details={"status_code": response.status, "api_version": "v2"},
                        duration_ms=duration_ms,
                    )

        # No generic exception handling; let errors propagate
