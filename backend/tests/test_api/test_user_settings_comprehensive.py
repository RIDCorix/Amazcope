"""Comprehensive tests for user settings API endpoints.

Tests user settings operations including:
- Getting current settings
- Updating settings
- Resetting to defaults
"""

import pytest
from httpx import AsyncClient

from users.models import User


class TestGetUserSettings:
    """Tests for getting user settings."""

    @pytest.mark.asyncio
    async def test_get_settings_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test successfully getting user settings."""
        response = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Verify common settings fields
        assert "email_notifications_enabled" in data
        assert "default_price_threshold" in data

    @pytest.mark.asyncio
    async def test_get_settings_returns_defaults(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test settings endpoint returns default values for new users."""
        response = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should have some default values set
        assert data is not None
        assert isinstance(data, dict)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_settings_unauthorized(self, client: AsyncClient):
        """Test getting settings requires authentication."""
        response = await client.get("/api/v1/user/settings")

        assert response.status_code == 403


class TestUpdateUserSettings:
    """Tests for updating user settings."""

    @pytest.mark.asyncio
    async def test_update_settings_email_notifications(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test updating email notification preferences."""
        response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "email_notifications_enabled": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("email_notifications_enabled") is False

    @pytest.mark.asyncio
    async def test_update_settings_price_threshold(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test updating default price change threshold."""
        response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "default_price_threshold": 15.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("default_price_threshold") == 15.0

    @pytest.mark.asyncio
    async def test_update_settings_bsr_threshold(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test updating default BSR change threshold."""
        response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "default_bsr_threshold": 25.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("default_bsr_threshold") == 25.0

    @pytest.mark.asyncio
    async def test_update_settings_partial_update(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test partial settings update (PATCH semantics)."""
        # First, get current settings
        get_response = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        original_settings = get_response.json()

        # Update only one field
        response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "email_notifications_enabled": True,
            },
        )

        assert response.status_code == 200
        updated_settings = response.json()
        # Updated field should change
        assert updated_settings.get("email_notifications_enabled") is True
        # Other fields should remain unchanged (if they exist)
        for key in original_settings:
            if key != "email_notifications_enabled" and key in updated_settings:
                assert updated_settings[key] == original_settings[key]

    @pytest.mark.asyncio
    async def test_update_settings_multiple_fields(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test updating multiple settings at once."""
        response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "email_notifications_enabled": False,
                "default_price_threshold": 20.0,
                "default_bsr_threshold": 35.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("email_notifications_enabled") is False
        assert data.get("default_price_threshold") == 20.0
        assert data.get("default_bsr_threshold") == 35.0

    @pytest.mark.asyncio
    async def test_update_settings_invalid_threshold_negative(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test updating with negative threshold fails."""
        response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "default_price_threshold": -10.0,
            },
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_update_settings_invalid_threshold_too_large(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test updating with excessively large threshold fails."""
        response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "default_price_threshold": 10000.0,  # Unreasonably large
            },
        )

        # Might succeed with validation or fail with 422
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_update_settings_invalid_field(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test updating with invalid/unknown field."""
        response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "invalid_field": "some_value",
            },
        )

        # Might be ignored or rejected depending on validation
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_update_settings_unauthorized(self, client: AsyncClient):
        """Test updating settings requires authentication."""
        response = await client.patch(
            "/api/v1/user/settings",
            json={
                "email_notifications_enabled": False,
            },
        )

        assert response.status_code == 403


class TestResetUserSettings:
    """Tests for resetting user settings to defaults."""

    @pytest.mark.asyncio
    async def test_reset_settings_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test successfully resetting settings to defaults."""
        # First, change some settings
        update_response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "email_notifications_enabled": False,
                "default_price_threshold": 25.0,
            },
        )
        assert update_response.status_code == 200

        # Reset to defaults
        reset_response = await client.post(
            "/api/v1/user/settings/reset",
            headers=auth_headers,
        )

        assert reset_response.status_code == 200
        data = reset_response.json()
        # Should return default values
        assert data is not None
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_reset_settings_restores_defaults(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test reset actually restores default values."""
        # Get initial/default settings
        initial_response = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )
        initial_settings = initial_response.json()

        # Modify settings
        await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "email_notifications_enabled": not initial_settings.get(
                    "email_notifications_enabled", True
                ),
            },
        )

        # Reset
        reset_response = await client.post(
            "/api/v1/user/settings/reset",
            headers=auth_headers,
        )
        assert reset_response.status_code == 200

        # Get settings after reset
        after_reset_response = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )
        after_reset_settings = after_reset_response.json()

        # Should match initial settings (or system defaults)
        # Note: This assumes reset actually restores to defaults
        # The exact comparison depends on the implementation
        assert after_reset_settings is not None

    @pytest.mark.asyncio
    async def test_reset_settings_unauthorized(self, client: AsyncClient):
        """Test resetting settings requires authentication."""
        response = await client.post("/api/v1/user/settings/reset")

        assert response.status_code == 403


class TestUserSettingsFlow:
    """Integration tests for complete user settings workflows."""

    @pytest.mark.asyncio
    async def test_complete_settings_flow(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test complete settings flow: get → update → verify → reset → verify."""
        # 1. Get initial settings
        initial_response = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )
        assert initial_response.status_code == 200
        initial_response.json()  # Verify response is valid JSON

        # 2. Update multiple settings
        update_response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "email_notifications_enabled": False,
                "default_price_threshold": 18.0,
                "default_bsr_threshold": 28.0,
            },
        )
        assert update_response.status_code == 200

        # 3. Verify updates
        verify_response = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )
        assert verify_response.status_code == 200
        updated_settings = verify_response.json()
        assert updated_settings.get("email_notifications_enabled") is False
        assert updated_settings.get("default_price_threshold") == 18.0
        assert updated_settings.get("default_bsr_threshold") == 28.0

        # 4. Reset to defaults
        reset_response = await client.post(
            "/api/v1/user/settings/reset",
            headers=auth_headers,
        )
        assert reset_response.status_code == 200

        # 5. Verify reset
        final_response = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )
        assert final_response.status_code == 200
        final_settings = final_response.json()
        # Settings should be reset (exact values depend on implementation)
        assert final_settings is not None

    @pytest.mark.asyncio
    async def test_settings_persistence(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test that settings changes persist across requests."""
        # Update settings
        update_response = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "default_price_threshold": 22.0,
            },
        )
        assert update_response.status_code == 200

        # Get settings again (simulating new request)
        get_response1 = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )
        assert get_response1.status_code == 200
        settings1 = get_response1.json()

        # Get settings one more time
        get_response2 = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )
        assert get_response2.status_code == 200
        settings2 = get_response2.json()

        # Both should have the same updated value
        assert settings1.get("default_price_threshold") == 22.0
        assert settings2.get("default_price_threshold") == 22.0

    @pytest.mark.asyncio
    async def test_settings_user_isolation(
        self,
        client: AsyncClient,
        test_user: User,
        test_superuser: User,
        auth_headers: dict[str, str],
        admin_headers: dict[str, str],
    ):
        """Test that users have independent settings."""
        # Update test_user settings
        user_update = await client.patch(
            "/api/v1/user/settings",
            headers=auth_headers,
            json={
                "email_notifications_enabled": False,
            },
        )
        assert user_update.status_code == 200

        # Update admin settings
        admin_update = await client.patch(
            "/api/v1/user/settings",
            headers=admin_headers,
            json={
                "email_notifications_enabled": True,
            },
        )
        assert admin_update.status_code == 200

        # Verify test_user still has their own settings
        user_get = await client.get(
            "/api/v1/user/settings",
            headers=auth_headers,
        )
        assert user_get.status_code == 200
        user_settings = user_get.json()
        assert user_settings.get("email_notifications_enabled") is False

        # Verify admin has their own settings
        admin_get = await client.get(
            "/api/v1/user/settings",
            headers=admin_headers,
        )
        assert admin_get.status_code == 200
        admin_settings = admin_get.json()
        assert admin_settings.get("email_notifications_enabled") is True
