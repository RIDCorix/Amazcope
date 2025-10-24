"""API endpoints for AI suggestion management."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_async_db, get_current_user
from optimization.models import (
    ActionStatus,
    Suggestion,
    SuggestionAction,
    SuggestionStatus,
)
from schemas.suggestion import (
    ActionApprovalRequest,
    ApplyActionRequest,
    SuggestionApprovalRequest,
    SuggestionListOut,
    SuggestionOut,
    SuggestionStats,
)
from users.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[SuggestionListOut])
async def list_suggestions(
    status_filter: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    product_id: UUID | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[SuggestionListOut]:
    """List all suggestions with optional filters.

    Args:
        status_filter: Filter by status (pending, approved, declined, etc.)
        priority: Filter by priority (low, medium, high, critical)
        category: Filter by category (pricing, content, tracking, etc.)
        product_id: Filter by product ID
        limit: Maximum number of results
        current_user: Current authenticated user

    Returns:
        List of suggestions
    """
    filters: dict[str, UUID | str] = {}
    if status_filter:
        filters["status"] = status_filter
    if priority:
        filters["priority"] = priority
    if category:
        filters["category"] = category
    if product_id:
        filters["product_id"] = product_id

    # Get suggestions with actions prefetched
    stmt = select(Suggestion).options(selectinload(Suggestion.actions))
    if filters:
        for key, value in filters.items():
            stmt = stmt.where(getattr(Suggestion, key) == value)
    stmt = stmt.order_by(Suggestion.created_at.desc()).limit(limit)
    result_obj = await db.execute(stmt)
    suggestions: list[Suggestion] = list(result_obj.scalars().all())

    # Build response
    result = []
    for suggestion in suggestions:
        action_count = len(suggestion.actions)
        # Add pending actions count
        pending_count = sum(1 for a in suggestion.actions if a.status == ActionStatus.PENDING)

        result.append(
            SuggestionListOut(
                id=suggestion.id,  # type: ignore[arg-type]
                title=suggestion.title,  # type: ignore[arg-type]
                description=suggestion.description,  # type: ignore[arg-type]
                product_id=suggestion.product_id,  # type: ignore[arg-type]
                priority=suggestion.priority,  # type: ignore[arg-type]
                category=suggestion.category,  # type: ignore[arg-type]
                status=suggestion.status,  # type: ignore[arg-type]
                confidence_score=suggestion.confidence_score,  # type: ignore[arg-type]
                created_at=suggestion.created_at,  # type: ignore[arg-type]
                action_count=action_count,
                pending_action_count=pending_count,
            )
        )

    return result


@router.post("/actions/review")
async def review_actions(
    request: ActionApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Approve or decline specific actions.

    Args:
        request: Action approval/decline request
        current_user: Current authenticated user

    Returns:
        Updated action statuses
    """
    if request.decision not in ["approved", "declined"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approved' or 'declined'",
        )

    # Get actions
    result = await db.execute(
        select(SuggestionAction).where(SuggestionAction.id.in_(request.action_ids))
    )
    actions = result.scalars().all()

    if not actions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No actions found with provided IDs",
        )

    # Update action statuses
    updated_count = 0
    applied_count = 0
    failed_count = 0

    # Map decision strings to ActionStatus enum values
    status_mapping = {
        "approved": ActionStatus.APPLIED,
        "declined": ActionStatus.REJECTED,
    }
    new_status = status_mapping[request.decision]

    for action in actions:
        action.status = new_status  # type: ignore[assignment]
        action.reviewed_by = current_user
        action.reviewed_at = datetime.utcnow()  # type: ignore[assignment]
        await db.commit()
        await db.refresh(action)
        updated_count += 1

        # Apply if approved and requested
        if request.decision == "approved" and request.apply_immediately:
            success = await action.apply(current_user)  # type: ignore[attr-defined]
            if success:
                applied_count += 1
            else:
                failed_count += 1

    return {
        "success": True,
        "updated_count": updated_count,
        "applied_count": applied_count,
        "failed_count": failed_count,
        "message": f"{updated_count} actions {request.decision}",
    }


@router.get("/{suggestion_id}", response_model=SuggestionOut)
async def get_suggestion(
    suggestion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Suggestion:
    """Get detailed suggestion information including all actions.

    Args:
        suggestion_id: Suggestion ID
        current_user: Current authenticated user

    Returns:
        Detailed suggestion with actions
    """
    suggestion: Suggestion = (
        await db.execute(
            select(Suggestion)
            .options(selectinload(Suggestion.actions))
            .where(Suggestion.id == suggestion_id)
        )
    ).scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion {suggestion_id} not found",
        )

    return suggestion


@router.post("/{suggestion_id}/review", response_model=SuggestionOut)
async def review_suggestion(
    suggestion_id: UUID,
    request: SuggestionApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Suggestion:
    """Review and approve/decline a suggestion.

    Args:
        suggestion_id: Suggestion ID
        request: Approval/decline request with action IDs
        current_user: Current authenticated user

    Returns:
        Updated suggestion status
    """
    suggestion = (
        await db.execute(
            select(Suggestion)
            .options(selectinload(Suggestion.actions))
            .where(Suggestion.id == suggestion_id)
        )
    ).scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion {suggestion_id} not found",
        )

    if suggestion.status != SuggestionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Suggestion already reviewed (status: {suggestion.status})",
        )

    # Update suggestion status
    suggestion.status = request.decision
    suggestion.reviewed_by = current_user
    suggestion.reviewed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(suggestion, ["actions"])  # Explicitly refresh actions relationship

    # Update action statuses
    if request.decision == "approved":
        # Approve all actions
        for action in suggestion.actions:
            action.status = ActionStatus.APPLIED
            action.reviewed_by = current_user
            action.reviewed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(action)

    elif request.decision == "declined":
        # Decline all actions
        for action in suggestion.actions:
            action.status = ActionStatus.REJECTED
            action.reviewed_by = current_user
            action.reviewed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(action)

    elif request.decision == "partially_approved":
        # Approve/decline specific actions
        for action in suggestion.actions:
            if action.id in request.approved_action_ids:
                action.status = ActionStatus.APPLIED
                action.reviewed_by = current_user
                action.reviewed_at = datetime.utcnow()
                await db.commit()
                await db.refresh(action)
            elif action.id in request.declined_action_ids:
                action.status = ActionStatus.REJECTED
                action.reviewed_by = current_user
                action.reviewed_at = datetime.utcnow()
                await db.commit()
                await db.refresh(action)

    # Apply actions if requested
    if request.apply_immediately and request.decision in [
        "approved",
        "partially_approved",
    ]:
        actions_to_apply = (
            [
                a
                for a in suggestion.actions
                if a.status == ActionStatus.APPLIED and a.id in request.approved_action_ids
            ]
            if request.decision == "partially_approved"
            else [a for a in suggestion.actions if a.status == ActionStatus.APPLIED]
        )

        applied_count = 0
        failed_count = 0

        for action in actions_to_apply:
            success = await action.apply(current_user)
            if success:
                applied_count += 1
            else:
                failed_count += 1

        logger.info(
            f"Applied {applied_count} actions, {failed_count} failed for suggestion {suggestion_id}"
        )

    return suggestion


@router.post("/actions/apply")
async def apply_actions(
    request: ApplyActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, bool | int | list[dict[str, str]]]:
    """Apply approved actions to products.

    Args:
        request: Apply actions request
        current_user: Current authenticated user

    Returns:
        Application results
    """
    # Get approved actions only
    result = await db.execute(
        select(SuggestionAction)
        .options(selectinload(SuggestionAction.suggestion).selectinload(Suggestion.product))
        .where(
            SuggestionAction.id.in_(request.action_ids),
            SuggestionAction.status == "approved",
        )
    )
    actions = result.scalars().all()

    if not actions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No approved actions found with provided IDs",
        )

    applied_count = 0
    failed_count = 0
    results: list[dict[str, str]] = []

    for action in actions:
        success = await action.apply(current_user)  # type: ignore[attr-defined]
        if success:
            applied_count += 1
            results.append(
                {
                    "action_id": str(action.id),  # type: ignore[arg-type]
                    "status": "applied",
                    "target_field": str(action.target_field),  # type: ignore[arg-type]
                }
            )
        else:
            failed_count += 1
            results.append(
                {
                    "action_id": str(action.id),  # type: ignore[arg-type]
                    "status": "failed",
                    "error": str(action.error_message) if action.error_message else "",  # type: ignore[arg-type]
                }
            )

    return {
        "success": True,
        "applied_count": applied_count,
        "failed_count": failed_count,
        "results": results,
    }


@router.get("/stats/overview", response_model=SuggestionStats)
async def get_suggestion_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> SuggestionStats:
    """Get overview statistics for suggestions.

    Args:
        current_user: Current authenticated user

    Returns:
        Suggestion statistics
    """
    all_suggestions = (await db.execute(select(Suggestion))).scalars().all()

    stats = SuggestionStats(
        total_suggestions=len(all_suggestions),
        pending=sum(1 for s in all_suggestions if s.status == "pending"),
        approved=sum(1 for s in all_suggestions if s.status == "approved"),
        rejected=sum(1 for s in all_suggestions if s.status == "rejected"),
        partially_approved=sum(1 for s in all_suggestions if s.status == "partially_approved"),
        by_category={},
        by_priority={},
    )

    # Count by category
    for suggestion in all_suggestions:
        stats.by_category[suggestion.category] = stats.by_category.get(suggestion.category, 0) + 1  # type: ignore[index,call-overload]
        stats.by_priority[suggestion.priority] = stats.by_priority.get(suggestion.priority, 0) + 1  # type: ignore[index,call-overload]

    return stats


@router.delete("/{suggestion_id}")
async def delete_suggestion(
    suggestion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, bool | str]:
    """Delete a suggestion (admin only, typically for cleaning up old suggestions).

    Args:
        suggestion_id: Suggestion ID
        current_user: Current authenticated user

    Returns:
        Deletion confirmation
    """
    suggestion = (
        await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    ).scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion {suggestion_id} not found",
        )

    await db.delete(suggestion)
    await db.commit()

    return {"success": True, "message": f"Suggestion {suggestion_id} deleted"}
