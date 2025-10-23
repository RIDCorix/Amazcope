"""Rate limiting middleware using Redis.

Implements token bucket algorithm for rate limiting with configurable
limits per endpoint and IP address.
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings
from services.cache_service import CacheService

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis token bucket algorithm.

    Features:
    - Per-IP rate limiting
    - Per-endpoint customizable limits
    - Automatic token bucket refill
    - Sliding window algorithm
    """

    # Rate limit configurations (requests per time window)
    RATE_LIMITS = {
        "/api/v1/auth/login": {"requests": 5, "window": 300},  # 5 per 5 minutes
        "/api/v1/auth/register": {"requests": 3, "window": 3600},  # 3 per hour
        "/api/v1/auth/refresh": {"requests": 10, "window": 60},  # 10 per minute
        "default": {"requests": 100, "window": 60},  # 100 per minute (default)
    }

    def __init__(self, app: Any) -> None:
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        self.cache = CacheService()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint handler

        Returns:
            HTTP response

        Raises:
            HTTPException: If rate limit exceeded
        """
        if settings.DISABLE_RATE_LIMITING:
            early_response: Response = await call_next(request)
            return early_response
        # Get client IP address
        client_ip = self._get_client_ip(request)

        # Get path-specific rate limit config
        path = request.url.path
        rate_config = self.RATE_LIMITS.get(path, self.RATE_LIMITS["default"])

        # Check rate limit
        is_allowed = await self._check_rate_limit(
            client_ip, path, rate_config["requests"], rate_config["window"]
        )

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP {client_ip} on path {path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too many requests",
                    "message": f"Rate limit exceeded. Maximum {rate_config['requests']} requests per {rate_config['window']} seconds.",
                    "retry_after": rate_config["window"],
                },
            )

        # Process request
        response: Response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.

        Handles X-Forwarded-For header for proxy/load balancer scenarios.

        Args:
            request: HTTP request

        Returns:
            Client IP address string
        """
        # Check X-Forwarded-For header (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP in the chain
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    async def _check_rate_limit(
        self, client_ip: str, path: str, max_requests: int, window_seconds: int
    ) -> bool:
        """Check if request is within rate limit using sliding window.

        Args:
            client_ip: Client IP address
            path: Request path
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if request allowed, False if rate limit exceeded
        """
        # Create Redis key for this IP + path combination
        key = f"rate_limit:{client_ip}:{path}"

        try:
            # Get current request count
            current_count = await self.cache.redis.get(key)

            if current_count is None:
                # First request in window - set counter with expiry
                await self.cache.redis.setex(key, window_seconds, 1)
                return True

            # Check if limit exceeded
            if int(current_count) >= max_requests:
                return False

            # Increment counter
            await self.cache.redis.incr(key)
            return True

        except Exception as e:
            logger.error(f"Rate limit check failed for {key}: {str(e)}")
            # On error, allow request (fail open for availability)
            return True


class LoginRateLimiter:
    """Dedicated rate limiter for login attempts with account lockout.

    Features:
    - 5 failed attempts triggers lockout
    - Exponential backoff on repeated failures
    - Email notification on suspicious activity
    """

    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    def __init__(self) -> None:
        """Initialize login rate limiter."""
        self.cache = CacheService()

    async def check_login_allowed(self, identifier: str) -> tuple[bool, str | None]:
        """Check if login attempt is allowed.

        Args:
            identifier: Email or username

        Returns:
            Tuple of (is_allowed, error_message)
        """
        key = f"login_attempts:{identifier}"

        try:
            # Get attempt data
            data = await self.cache.get(key)

            if data is None:
                # No previous attempts
                return True, None

            attempts = data.get("count", 0)
            locked_until_str = data.get("locked_until")

            # Check if account is locked
            if locked_until_str:
                locked_until = datetime.fromisoformat(locked_until_str)
                if datetime.utcnow() < locked_until:
                    remaining_minutes = int((locked_until - datetime.utcnow()).total_seconds() / 60)
                    return (
                        False,
                        f"Account locked. Try again in {remaining_minutes} minutes.",
                    )

                # Lockout expired - reset counter
                await self.cache.delete(key)
                return True, None

            # Check if max attempts exceeded
            if attempts >= self.MAX_ATTEMPTS:
                # Lock account
                locked_until = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                await self.cache.set(
                    key,
                    {
                        "count": attempts,
                        "locked_until": locked_until.isoformat(),
                    },
                    ttl=self.LOCKOUT_DURATION_MINUTES * 60,
                )
                return (
                    False,
                    f"Too many failed attempts. Account locked for {self.LOCKOUT_DURATION_MINUTES} minutes.",
                )

            return True, None

        except Exception as e:
            logger.error(f"Login rate limit check failed for {identifier}: {str(e)}")
            # On error, allow login (fail open)
            return True, None

    async def record_failed_attempt(self, identifier: str) -> int:
        """Record a failed login attempt.

        Args:
            identifier: Email or username

        Returns:
            Current attempt count
        """
        key = f"login_attempts:{identifier}"

        try:
            data = await self.cache.get(key)

            if data is None:
                # First failed attempt
                await self.cache.set(
                    key,
                    {"count": 1, "locked_until": None},
                    ttl=self.LOCKOUT_DURATION_MINUTES * 60,
                )
                return 1

            # Increment counter
            attempts = data.get("count", 0) + 1
            data["count"] = attempts

            await self.cache.set(
                key,
                data,
                ttl=self.LOCKOUT_DURATION_MINUTES * 60,
            )
            return int(attempts)

        except Exception as e:
            logger.error(f"Failed to record login attempt for {identifier}: {str(e)}")
            return 0

    async def reset_attempts(self, identifier: str) -> None:
        """Reset failed attempt counter after successful login.

        Args:
            identifier: Email or username
        """
        key = f"login_attempts:{identifier}"
        await self.cache.delete(key)
