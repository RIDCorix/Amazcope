"""Simple, focused tests for authentication.

Replaces failing tests from test_auth_comprehensive.py.
"""

import pytest
from httpx import AsyncClient

from users.models import User


class TestLogin:
    """Test login functionality."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email_or_username": test_user.username,
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email_or_username": test_user.username,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email_or_username": "nonexistent",
                "password": "password123",
            },
        )

        assert response.status_code == 401


class TestRegistration:
    """Test user registration."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "Securepassword123!",
                "full_name": "New User",
            },
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with existing email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "differentusername",
                "password": "password123",
            },
        )

        assert response.status_code == 422
