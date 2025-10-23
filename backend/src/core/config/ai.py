import time

from pydantic_settings import BaseSettings

from system.checks import BaseCheck, CheckResult
from system.registries import dependency_registry


class AISettings(BaseSettings):
    OPENAI_API_KEY: str = ""


@dependency_registry.register()
class OpenAITest(BaseCheck):
    """Test OpenAI service connectivity."""

    name = "openai"

    async def test(self) -> CheckResult:
        """Test OpenAI service connection."""
        from core.config import settings

        start_time = time.time()

        if not hasattr(settings, "OPENAI_API_KEY") or not settings.OPENAI_API_KEY:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name=self.name,
                status="warning",
                message="OpenAI API key not configured",
                details={"configured": False, "service": "OpenAI"},
                duration_ms=duration_ms,
            )

        try:
            try:
                import aiohttp
            except ImportError:
                duration_ms = (time.time() - start_time) * 1000
                return CheckResult(
                    name=self.name,
                    status="error",
                    message="aiohttp not installed - required for OpenAI API testing",
                    details={
                        "error_type": "ImportError",
                        "required_package": "aiohttp",
                    },
                    duration_ms=duration_ms,
                )

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                }

                # Test API connectivity with a simple request to list models
                async with session.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    duration_ms = (time.time() - start_time) * 1000

                    if response.status == 200:
                        models_data = await response.json()
                        model_count = len(models_data.get("data", []))
                        return CheckResult(
                            name=self.name,
                            status="success",
                            message="OpenAI service connection successful",
                            details={
                                "status_code": response.status,
                                "available_models": model_count,
                                "api_version": "v1",
                            },
                            duration_ms=duration_ms,
                        )
                    else:
                        return CheckResult(
                            name=self.name,
                            status="error",
                            message=f"OpenAI service returned status {response.status}",
                            details={
                                "status_code": response.status,
                                "api_version": "v1",
                            },
                            duration_ms=duration_ms,
                        )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name=self.name,
                status="error",
                message=f"OpenAI service connection failed: {str(e)}",
                details={"error_type": type(e).__name__, "api_version": "v1"},
                duration_ms=duration_ms,
            )
