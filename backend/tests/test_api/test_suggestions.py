"""Tests for AI suggestions API endpoints.

Tests all suggestion management endpoints including:
- List suggestions with filters
- Get suggestion details
- Review suggestions (approve/decline/partial)
- Review individual actions
- Apply actions
- Get suggestion statistics
- Delete suggestions
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from optimization.models import (
    ActionStatus,
    ActionType,
    Suggestion,
    SuggestionAction,
    SuggestionCategory,
    SuggestionPriority,
    SuggestionStatus,
)
from products.models import Product
from users.models import User


@pytest.mark.asyncio
class TestListSuggestions:
    """Test GET /api/v1/suggestions endpoint."""

    async def test_list_all_suggestions(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test listing all suggestions without filters."""
        # Create test product
        product = Product(
            asin="B07XJ8C8F5",
            marketplace="com",
            title="Test Product",
            url="https://amazon.com/dp/B07XJ8C8F5",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        # Create suggestions
        suggestion1 = Suggestion(
            title="Price Optimization",
            description="Consider lowering price",
            reasoning="Market analysis shows lower price point would increase sales",
            product_id=product.id,
            category=SuggestionCategory.PRICING,
            priority=SuggestionPriority.HIGH,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
            confidence_score=0.85,
        )
        suggestion2 = Suggestion(
            title="Content Improvement",
            description="Enhance product title",
            reasoning="Title optimization for better search visibility",
            product_id=product.id,
            category=SuggestionCategory.CONTENT,
            priority=SuggestionPriority.MEDIUM,
            status=SuggestionStatus.APPROVED,
            ai_model="gpt-4",
            confidence_score=0.75,
        )
        db_session.add_all([suggestion1, suggestion2])
        await db_session.commit()

        # Add actions to suggestions
        action1 = SuggestionAction(
            suggestion_id=suggestion1.id,
            action_type=ActionType.UPDATE_PRICE,
            target_field="price",
            current_value="29.99",
            proposed_value="24.99",
            reasoning="Competitive pricing analysis",
            status=ActionStatus.PENDING,
        )
        action2 = SuggestionAction(
            suggestion_id=suggestion2.id,
            action_type=ActionType.UPDATE_TITLE,
            target_field="title",
            current_value="Product Name",
            proposed_value="Enhanced Product Name with Keywords",
            reasoning="SEO optimization",
            status=ActionStatus.APPLIED,
        )
        db_session.add_all([action1, action2])
        await db_session.commit()

        # Test list endpoint
        response = await client.get("/api/v1/suggestions/", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Verify first suggestion
        assert data[0]["title"] == "Content Improvement"
        assert data[0]["status"] == SuggestionStatus.APPROVED
        assert data[0]["action_count"] == 1
        assert data[0]["pending_action_count"] == 0

    async def test_list_suggestions_with_status_filter(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test filtering suggestions by status."""
        product = Product(
            asin="B07XJ8C8F6",
            marketplace="com",
            title="Test Product 2",
            url="https://amazon.com/dp/B07XJ8C8F6",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        # Create suggestions with different statuses
        pending = Suggestion(
            title="Pending Suggestion",
            description="Pending",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.PRICING,
            priority=SuggestionPriority.MEDIUM,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
        )
        approved = Suggestion(
            title="Approved Suggestion",
            description="Approved",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.CONTENT,
            priority=SuggestionPriority.HIGH,
            status=SuggestionStatus.APPROVED,
            ai_model="gpt-4",
        )
        db_session.add_all([pending, approved])
        await db_session.commit()

        # Filter by pending status
        response = await client.get(
            "/api/v1/suggestions/?status_filter=pending", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == SuggestionStatus.PENDING

    async def test_list_suggestions_with_category_filter(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test filtering suggestions by category."""
        product = Product(
            asin="B07XJ8C8F7",
            marketplace="com",
            title="Test Product 3",
            url="https://amazon.com/dp/B07XJ8C8F7",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        pricing = Suggestion(
            title="Pricing Suggestion",
            description="Price",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.PRICING,
            priority=SuggestionPriority.HIGH,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
        )
        content = Suggestion(
            title="Content Suggestion",
            description="Content",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.CONTENT,
            priority=SuggestionPriority.MEDIUM,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
        )
        db_session.add_all([pricing, content])
        await db_session.commit()

        # Filter by pricing category
        response = await client.get("/api/v1/suggestions/?category=pricing", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == SuggestionCategory.PRICING

    async def test_list_suggestions_with_limit(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test limiting number of suggestions returned."""
        product = Product(
            asin="B07XJ8C8F8",
            marketplace="com",
            title="Test Product 4",
            url="https://amazon.com/dp/B07XJ8C8F8",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        # Create 5 suggestions
        suggestions = [
            Suggestion(
                title=f"Suggestion {i}",
                description=f"Description {i}",
                reasoning="Test",
                product_id=product.id,
                category=SuggestionCategory.PRICING,
                priority=SuggestionPriority.MEDIUM,
                status=SuggestionStatus.PENDING,
                ai_model="gpt-4",
            )
            for i in range(5)
        ]
        db_session.add_all(suggestions)
        await db_session.commit()

        # Limit to 3 results
        response = await client.get("/api/v1/suggestions/?limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


@pytest.mark.asyncio
class TestGetSuggestion:
    """Test GET /api/v1/suggestions/{suggestion_id} endpoint."""

    async def test_get_suggestion_success(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test getting detailed suggestion with actions."""
        product = Product(
            asin="B07XJ8C8F9",
            marketplace="com",
            title="Test Product 5",
            url="https://amazon.com/dp/B07XJ8C8F9",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        suggestion = Suggestion(
            title="Test Suggestion",
            description="Test Description",
            reasoning="Test Reasoning",
            product_id=product.id,
            category=SuggestionCategory.PRICING,
            priority=SuggestionPriority.HIGH,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
            confidence_score=0.9,
        )
        db_session.add(suggestion)
        await db_session.commit()
        await db_session.refresh(suggestion)

        # Add actions
        action = SuggestionAction(
            suggestion_id=suggestion.id,
            action_type=ActionType.UPDATE_PRICE,
            target_field="price",
            current_value="29.99",
            proposed_value="24.99",
            reasoning="Price optimization",
            status=ActionStatus.PENDING,
        )
        db_session.add(action)
        await db_session.commit()

        # Get suggestion
        response = await client.get(f"/api/v1/suggestions/{suggestion.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(suggestion.id)
        assert data["title"] == "Test Suggestion"
        assert data["confidence_score"] == 0.9
        assert len(data["actions"]) == 1
        assert data["actions"][0]["target_field"] == "price"

    async def test_get_suggestion_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent suggestion."""
        fake_id = uuid4()
        response = await client.get(f"/api/v1/suggestions/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestReviewSuggestion:
    """Test POST /api/v1/suggestions/{suggestion_id}/review endpoint."""

    async def test_approve_suggestion(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test approving a suggestion."""
        product = Product(
            asin="B07XJ8C9F0",
            marketplace="com",
            title="Test Product 6",
            url="https://amazon.com/dp/B07XJ8C9F0",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        suggestion = Suggestion(
            title="Approve Test",
            description="Test",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.PRICING,
            priority=SuggestionPriority.MEDIUM,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
        )
        db_session.add(suggestion)
        await db_session.commit()
        await db_session.refresh(suggestion)

        action = SuggestionAction(
            suggestion_id=suggestion.id,
            action_type=ActionType.UPDATE_PRICE,
            target_field="price",
            current_value="29.99",
            proposed_value="24.99",
            reasoning="Test",
            status=ActionStatus.PENDING,
        )
        db_session.add(action)
        await db_session.commit()

        # Approve suggestion
        response = await client.post(
            f"/api/v1/suggestions/{suggestion.id}/review",
            headers=auth_headers,
            json={
                "suggestion_id": str(suggestion.id),
                "decision": "approved",
                "approved_action_ids": [],
                "declined_action_ids": [],
                "apply_immediately": False,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == SuggestionStatus.APPROVED
        assert data["reviewed_at"] is not None

    async def test_decline_suggestion(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test declining a suggestion."""
        product = Product(
            asin="B07XJ8C9F1",
            marketplace="com",
            title="Test Product 7",
            url="https://amazon.com/dp/B07XJ8C9F1",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        suggestion = Suggestion(
            title="Decline Test",
            description="Test",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.CONTENT,
            priority=SuggestionPriority.LOW,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
        )
        db_session.add(suggestion)
        await db_session.commit()
        await db_session.refresh(suggestion)

        # Decline suggestion (use "rejected" to match SuggestionStatus enum)
        response = await client.post(
            f"/api/v1/suggestions/{suggestion.id}/review",
            headers=auth_headers,
            json={
                "suggestion_id": str(suggestion.id),
                "decision": "rejected",
                "approved_action_ids": [],
                "declined_action_ids": [],
                "apply_immediately": False,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == SuggestionStatus.REJECTED

    async def test_partially_approve_suggestion(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test partially approving a suggestion (approve some actions, decline others)."""
        product = Product(
            asin="B07XJ8C9F2",
            marketplace="com",
            title="Test Product 8",
            url="https://amazon.com/dp/B07XJ8C9F2",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        suggestion = Suggestion(
            title="Partial Test",
            description="Test",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.CONTENT,
            priority=SuggestionPriority.MEDIUM,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
        )
        db_session.add(suggestion)
        await db_session.commit()
        await db_session.refresh(suggestion)

        # Add multiple actions
        action1 = SuggestionAction(
            suggestion_id=suggestion.id,
            action_type=ActionType.UPDATE_TITLE,
            target_field="title",
            current_value="Old Title",
            proposed_value="New Title",
            reasoning="SEO",
            status=ActionStatus.PENDING,
        )
        action2 = SuggestionAction(
            suggestion_id=suggestion.id,
            action_type=ActionType.UPDATE_TITLE,
            target_field="description",
            current_value="Old Desc",
            proposed_value="New Desc",
            reasoning="Better description",
            status=ActionStatus.PENDING,
        )
        db_session.add_all([action1, action2])
        await db_session.commit()
        await db_session.refresh(action1)
        await db_session.refresh(action2)

        # Partially approve (approve action1, decline action2)
        response = await client.post(
            f"/api/v1/suggestions/{suggestion.id}/review",
            headers=auth_headers,
            json={
                "suggestion_id": str(suggestion.id),
                "decision": "partially_approved",
                "approved_action_ids": [str(action1.id)],
                "declined_action_ids": [str(action2.id)],
                "apply_immediately": False,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == SuggestionStatus.PARTIALLY_APPROVED

    async def test_review_already_reviewed_suggestion(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test that reviewing an already-reviewed suggestion fails."""
        product = Product(
            asin="B07XJ8C9F3",
            marketplace="com",
            title="Test Product 9",
            url="https://amazon.com/dp/B07XJ8C9F3",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        suggestion = Suggestion(
            title="Already Reviewed",
            description="Test",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.PRICING,
            priority=SuggestionPriority.HIGH,
            status=SuggestionStatus.APPROVED,  # Already approved
            ai_model="gpt-4",
        )
        db_session.add(suggestion)
        await db_session.commit()
        await db_session.refresh(suggestion)

        # Try to review again
        response = await client.post(
            f"/api/v1/suggestions/{suggestion.id}/review",
            headers=auth_headers,
            json={
                "suggestion_id": str(suggestion.id),
                "decision": "declined",
                "apply_immediately": False,
            },
        )
        assert response.status_code == 400
        assert "already reviewed" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestReviewActions:
    """Test POST /api/v1/suggestions/actions/review endpoint."""

    async def test_approve_actions(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test approving specific actions."""
        product = Product(
            asin="B07XJ8C9F4",
            marketplace="com",
            title="Test Product 10",
            url="https://amazon.com/dp/B07XJ8C9F4",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        suggestion = Suggestion(
            title="Action Review Test",
            description="Test",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.CONTENT,
            priority=SuggestionPriority.MEDIUM,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
        )
        db_session.add(suggestion)
        await db_session.commit()
        await db_session.refresh(suggestion)

        action = SuggestionAction(
            suggestion_id=suggestion.id,
            action_type=ActionType.UPDATE_TITLE,
            target_field="title",
            current_value="Old",
            proposed_value="New",
            reasoning="Test",
            status=ActionStatus.PENDING,
        )
        db_session.add(action)
        await db_session.commit()
        await db_session.refresh(action)

        # Approve action
        response = await client.post(
            "/api/v1/suggestions/actions/review",
            headers=auth_headers,
            json={
                "action_ids": [str(action.id)],
                "decision": "approved",
                "apply_immediately": False,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 1

    async def test_review_actions_invalid_decision(self, client: AsyncClient, auth_headers: dict):
        """Test that invalid decision fails."""
        response = await client.post(
            "/api/v1/suggestions/actions/review",
            headers=auth_headers,
            json={
                "action_ids": ["550e8400-e29b-41d4-a716-446655440000"],  # Valid UUID format
                "decision": "invalid",
                "apply_immediately": False,
            },
        )
        assert response.status_code == 400  # Endpoint raises 400 Bad Request for invalid decision
        detail = response.json()["detail"]
        # Should get an error about decision not being valid (invalid is not "approved" or "declined")
        assert "'approved' or 'declined'" in str(detail).lower() or "invalid" in str(detail).lower()


@pytest.mark.asyncio
class TestGetSuggestionStats:
    """Test GET /api/v1/suggestions/stats/overview endpoint."""

    async def test_get_stats(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test getting suggestion statistics."""
        product = Product(
            asin="B07XJ8C9F5",
            marketplace="com",
            title="Test Product 11",
            url="https://amazon.com/dp/B07XJ8C9F5",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        # Create suggestions with various statuses
        pending = Suggestion(
            title="Pending",
            description="Test",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.PRICING,
            priority=SuggestionPriority.HIGH,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
        )
        approved = Suggestion(
            title="Approved",
            description="Test",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.CONTENT,
            priority=SuggestionPriority.MEDIUM,
            status=SuggestionStatus.APPROVED,
            ai_model="gpt-4",
        )
        rejected = Suggestion(
            title="Rejected",
            description="Test",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.TRACKING,
            priority=SuggestionPriority.LOW,
            status=SuggestionStatus.REJECTED,
            ai_model="gpt-4",
        )
        db_session.add_all([pending, approved, rejected])
        await db_session.commit()

        # Get stats
        response = await client.get("/api/v1/suggestions/stats/overview", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["total_suggestions"] == 3
        assert data["pending"] == 1
        assert data["approved"] == 1
        assert data["rejected"] == 1
        assert SuggestionCategory.PRICING in data["by_category"]
        assert SuggestionPriority.HIGH in data["by_priority"]


@pytest.mark.asyncio
class TestDeleteSuggestion:
    """Test DELETE /api/v1/suggestions/{suggestion_id} endpoint."""

    async def test_delete_suggestion(
        self, client: AsyncClient, auth_headers: dict, test_user: User, db_session
    ):
        """Test deleting a suggestion."""
        product = Product(
            asin="B07XJ8C9F6",
            marketplace="com",
            title="Test Product 12",
            url="https://amazon.com/dp/B07XJ8C9F6",
            created_by_id=test_user.id,
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        suggestion = Suggestion(
            title="Delete Test",
            description="Test",
            reasoning="Test",
            product_id=product.id,
            category=SuggestionCategory.PRICING,
            priority=SuggestionPriority.MEDIUM,
            status=SuggestionStatus.PENDING,
            ai_model="gpt-4",
        )
        db_session.add(suggestion)
        await db_session.commit()
        await db_session.refresh(suggestion)

        # Delete suggestion
        response = await client.delete(f"/api/v1/suggestions/{suggestion.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

    async def test_delete_nonexistent_suggestion(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent suggestion."""
        fake_id = uuid4()
        response = await client.delete(f"/api/v1/suggestions/{fake_id}", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestSuggestionAuth:
    """Test authentication requirements for suggestions endpoints."""

    async def test_requires_authentication(self, client: AsyncClient):
        """Test that all endpoints require authentication."""
        endpoints = [
            ("GET", "/api/v1/suggestions/"),
            ("GET", f"/api/v1/suggestions/{uuid4()}"),
            ("POST", f"/api/v1/suggestions/{uuid4()}/review"),
            ("POST", "/api/v1/suggestions/actions/review"),
            ("GET", "/api/v1/suggestions/stats/overview"),
            ("DELETE", f"/api/v1/suggestions/{uuid4()}"),
        ]

        for method, url in endpoints:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json={})
            elif method == "DELETE":
                response = await client.delete(url)

            assert response.status_code in [401, 403], (
                f"Endpoint {method} {url} should require auth"
            )
