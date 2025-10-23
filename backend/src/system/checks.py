from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    """Result of a dependency test."""

    name: str
    status: str  # "success", "warning", "error"
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float


class BaseCheck(ABC):
    """Base class for dependency tests."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the dependency being tested."""
        pass

    @abstractmethod
    async def test(self) -> CheckResult:
        """Test the dependency and return result."""
        pass
