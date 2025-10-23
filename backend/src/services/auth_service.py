"""Authentication service using SQLAlchemy.

Provides user authentication, registration, and token management with
comprehensive security features:
- Email/username authentication
- Account lockout after failed attempts
- Suspicious login detection
- Email notifications for security events
"""

import re
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from middleware.rate_limit import LoginRateLimiter
from services.security_notification_service import SecurityNotificationService
from users.models import User
from users.schemas import LoginRequest, TokenResponse, UserCreate, UserOut

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for user authentication and management with security features."""

    def __init__(self, db: AsyncSession):
        """Initialize authentication service.

        Args:
            db: Database session
        """
        self.db = db
        self.login_limiter = LoginRateLimiter()
        self.security_notifier = SecurityNotificationService()

    # Email validation regex
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format.

        Args:
            email: Email address to validate

        Returns:
            True if valid email format, False otherwise
        """
        return bool(AuthService.EMAIL_REGEX.match(email))

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str | None]:
        """Validate password strength requirements.

        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, None

    async def get_user(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email_or_username(self, identifier: str) -> User | None:
        """Get user by email or username.

        Args:
            identifier: Email or username

        Returns:
            User if found, None otherwise
        """
        # Check if identifier is email format
        if self.is_valid_email(identifier):
            return await self.get_user_by_email(identifier)

        # Otherwise treat as username
        return await self.get_user_by_username(identifier)

    async def create_user(self, user: UserCreate) -> User:
        """Create a new user account."""
        hashed_password = hash_password(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            full_name=user.full_name,
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def register_user(self, user: UserCreate) -> User:
        """Register a new user with validation.

        Args:
            user: User registration data

        Returns:
            Created user

        Raises:
            HTTPException: If validation fails or user exists
        """
        # Validate password strength
        is_valid, error_msg = self.validate_password_strength(user.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Check if email already exists
        existing_user = await self.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check if username already exists
        existing_username = await self.get_user_by_username(user.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

        return await self.create_user(user)

    async def authenticate_user(
        self,
        identifier: str,
        password: str,
        ip_address: str | None = None,
    ) -> User:
        """Authenticate user with email/username and password.

        Includes:
        - Rate limiting check
        - Account lockout check
        - Failed attempt tracking
        - Suspicious login detection
        - Email notifications

        Args:
            identifier: Email or username
            password: Plain text password
            ip_address: Client IP address for security tracking

        Returns:
            Authenticated user

        Raises:
            HTTPException: If authentication fails or account locked
        """
        # Get user by email or username
        user = await self.get_user_by_email_or_username(identifier)

        if not user:
            # Record failed attempt even if user doesn't exist
            # (prevents username enumeration timing attacks)
            await self.login_limiter.record_failed_attempt(identifier)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive. Please contact support.",
            )

        # Check if account is locked
        if user.account_locked_until:
            if datetime.utcnow() < user.account_locked_until:
                remaining = (user.account_locked_until - datetime.utcnow()).total_seconds() / 60
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked. Try again in {int(remaining)} minutes.",
                )
            else:
                # Lockout expired - reset
                user.account_locked_until = None
                user.failed_login_attempts = 0
                await self.db.commit()

        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            user.last_failed_login_at = datetime.utcnow()

            # Check if should lock account (5 failed attempts)
            if user.failed_login_attempts >= 5:
                user.account_locked_until = datetime.utcnow() + timedelta(minutes=15)

                # Send lockout notification
                await self.security_notifier.send_account_lockout_notification(
                    user_email=user.email,
                    username=user.username,
                    lockout_duration_minutes=15,
                    failed_attempts=user.failed_login_attempts,
                )

            await self.db.commit()

            # Record in Redis for rate limiting
            attempts = await self.login_limiter.record_failed_attempt(identifier)

            # Send suspicious activity alert after 3 failed attempts
            if attempts >= 3:
                await self.security_notifier.send_suspicious_login_alert(
                    user_email=user.email,
                    username=user.username,
                    ip_address=ip_address or "unknown",
                    timestamp=datetime.utcnow(),
                    details={"attempts": attempts},
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Successful authentication

        # Check for suspicious activity (login from new IP)
        if ip_address and user.last_login_ip and ip_address != user.last_login_ip:
            await self.security_notifier.send_successful_login_from_new_location(
                user_email=user.email,
                username=user.username,
                ip_address=ip_address,
                location="Unknown location",  # TODO: Add IP geolocation
                device="Unknown device",  # TODO: Add user-agent parsing
            )

        # Update user login info
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        user.last_failed_login_at = None
        await self.db.commit()

        # Reset rate limiter
        await self.login_limiter.reset_attempts(identifier)

        return user

    async def login_user(
        self,
        credentials: LoginRequest,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Login user and return tokens.

        Args:
            credentials: Login credentials (email/username + password)
            ip_address: Client IP address for security tracking

        Returns:
            TokenResponse with access/refresh tokens and user data
        """
        user = await self.authenticate_user(
            credentials.email_or_username,
            credentials.password,
            ip_address,
        )

        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserOut.model_validate(user),
        )

    async def refresh_token(self, user: User) -> TokenResponse:
        """Refresh access token for user."""
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserOut.model_validate(user),
        )

    async def logout(self, user: User) -> None:
        """Logout user (token invalidation handled by client)."""
        # In a stateless JWT system, logout is typically handled client-side
        # by removing the token. For server-side token blacklisting,
        # implement token blacklist logic here.
        pass
