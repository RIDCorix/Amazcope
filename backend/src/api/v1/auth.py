"""Authentication API endpoints.

Provides user registration, login, token refresh, and profile management.
"""

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_async_db, get_current_user
from services.auth_service import AuthService
from users.models import User
from users.schemas import LoginRequest, TokenResponse, UserCreate, UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Register a new user account.

    Creates a new user account with the provided information.
    Password is automatically hashed before storage.
    """
    auth_service = AuthService(db)
    user = await auth_service.register_user(user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login_user(
    credentials: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """Authenticate user and return access tokens.

    Security features:
    - Email or username authentication
    - Rate limiting (5 attempts per 5 minutes)
    - Account lockout after 5 failed attempts
    - IP tracking for suspicious activity detection
    - Email notifications for security events

    Args:
        credentials: User login credentials (email/username + password)
        request: HTTP request for IP address extraction

    Returns:
        TokenResponse: Access and refresh tokens with user data

    Raises:
        HTTPException: If credentials invalid, account locked, or rate limited
    """

    auth_service = AuthService(db)

    # Extract client IP address
    client_ip = request.client.host if request.client else None
    if not client_ip:
        # Check X-Forwarded-For header for proxy/load balancer scenarios
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

    return await auth_service.login_user(credentials, ip_address=client_ip)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> TokenResponse:
    """Refresh access token using user's current session.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        TokenResponse: New access and refresh tokens
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_token(current_user)


@router.get("/profile", response_model=UserOut)
async def get_profile(current_user: User = Depends(get_current_user)) -> User:
    """Get current user profile.

    Args:
        current_user: Currently authenticated user

    Returns:
        UserOut: User profile information
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, str]:
    """Logout current user.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        dict: Success message
    """
    auth_service = AuthService(db)
    await auth_service.logout(current_user)
    return {"message": "Successfully logged out"}
