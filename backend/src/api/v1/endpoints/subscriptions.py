"""Subscription endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.api.deps import get_current_user, get_subscription_service
from src.services.subscription_service import SubscriptionService
from src.domain.entities.user import UserEntity

router = APIRouter(prefix="/subscriptions")


class CreateSubscriptionRequest(BaseModel):
    strategy_id: str
    params: dict | None = None
    channels: list[str] | None = None
    cooldown_seconds: int | None = None


class UpdateSubscriptionRequest(BaseModel):
    params: dict | None = None
    channels: list[str] | None = None
    cooldown_seconds: int | None = None


class SubscriptionResponse(BaseModel):
    id: str
    strategy_id: str
    params: dict
    channels: list[str]
    cooldown_seconds: int
    status: str
    last_signal_at: str | None
    signal_count: int
    created_at: str | None


class SubscriptionsListResponse(BaseModel):
    items: list[SubscriptionResponse]
    total: int


def to_response(entity) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=str(entity.id),
        strategy_id=entity.strategy_id,
        params=entity.params,
        channels=entity.channels,
        cooldown_seconds=entity.cooldown_seconds,
        status=entity.status.value,
        last_signal_at=entity.last_signal_at.isoformat() if entity.last_signal_at else None,
        signal_count=entity.signal_count,
        created_at=entity.created_at.isoformat() if entity.created_at else None,
    )


@router.get("", response_model=SubscriptionsListResponse)
async def list_subscriptions(
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    active_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List user's subscriptions."""
    subs = await subscription_service.get_user_subscriptions(
        user_id=current_user.id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )

    return SubscriptionsListResponse(
        items=[to_response(s) for s in subs],
        total=len(subs),
    )


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    """Create a new subscription."""
    sub = await subscription_service.create_subscription(
        user_id=current_user.id,
        strategy_id=request.strategy_id,
        params=request.params,
        channels=request.channels,
        cooldown_seconds=request.cooldown_seconds,
    )

    return to_response(sub)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    """Get subscription details."""
    sub = await subscription_service.get_by_id(subscription_id, current_user.id)
    return to_response(sub)


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: UUID,
    request: UpdateSubscriptionRequest,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    """Update subscription settings."""
    sub = await subscription_service.update_subscription(
        subscription_id=subscription_id,
        user_id=current_user.id,
        params=request.params,
        channels=request.channels,
        cooldown_seconds=request.cooldown_seconds,
    )

    return to_response(sub)


@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
async def pause_subscription(
    subscription_id: UUID,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    """Pause a subscription."""
    sub = await subscription_service.pause(subscription_id, current_user.id)
    return to_response(sub)


@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
async def resume_subscription(
    subscription_id: UUID,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    """Resume a subscription."""
    sub = await subscription_service.resume(subscription_id, current_user.id)
    return to_response(sub)


@router.delete("/{subscription_id}")
async def cancel_subscription(
    subscription_id: UUID,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    """Cancel a subscription."""
    await subscription_service.cancel(subscription_id, current_user.id)
    return {"message": "Subscription cancelled"}
