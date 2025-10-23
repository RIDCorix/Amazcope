from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return str(pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bool(pwd_context.verify(plain_password, hashed_password))


# JWT token generation
def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY is not configured")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.utcnow().timestamp(),  # Issued at timestamp (with microseconds)
            "jti": str(uuid4()),  # Unique JWT ID
        }
    )
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return str(encoded_jwt)


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT refresh token with longer expiration.

    Args:
        data: Data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT refresh token
    """
    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY is not configured")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow().timestamp(),  # Issued at timestamp (with microseconds)
            "jti": str(uuid4()),  # Unique JWT ID
        }
    )
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return str(encoded_jwt)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT access token."""
    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY is not configured")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return dict(payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        dict: Token payload if valid, None if invalid
    """
    if not settings.SECRET_KEY:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return dict(payload) if payload else None
    except JWTError:
        return None
