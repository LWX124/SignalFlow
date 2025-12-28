"""Notification endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.api.deps import get_current_user, get_notification_service
from src.services.notification_service import NotificationService
from src.domain.entities.user import UserEntity

router = APIRouter(prefix="/notifications")


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    content: str | None
    link: str | None
    is_read: bool
    created_at: str


class NotificationsListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


@router.get("", response_model=NotificationsListResponse)
async def list_notifications(
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    unread_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List user's notifications."""
    notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )

    unread_count = await notification_service.get_unread_count(current_user.id)

    return NotificationsListResponse(
        items=[
            NotificationResponse(
                id=str(n.id),
                type=n.type.value,
                title=n.title,
                content=n.content,
                link=n.link,
                is_read=n.is_read,
                created_at=n.created_at.isoformat(),
            )
            for n in notifications
        ],
        total=len(notifications),
        unread_count=unread_count,
    )


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: UUID,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
):
    """Mark a notification as read."""
    await notification_service.mark_as_read(notification_id, current_user.id)
    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_as_read(
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
):
    """Mark all notifications as read."""
    count = await notification_service.mark_all_as_read(current_user.id)
    return {"message": f"{count} notifications marked as read"}


@router.get("/unread-count")
async def get_unread_count(
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
):
    """Get unread notification count."""
    count = await notification_service.get_unread_count(current_user.id)
    return {"unread_count": count}
