"""Notification service."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from src.infra.database.models import Notification, DeliveryPlan
from src.core.constants import NotificationType, DeliveryStatus, DeliveryChannel


class NotificationService:
    """Service for notification operations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        content: str | None = None,
        link: str | None = None,
        metadata: dict | None = None,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            content=content,
            link=link,
            metadata_=metadata or {},
        )
        self._session.add(notification)
        await self._session.flush()
        await self._session.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Notification]:
        """Get user's notifications."""
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)

        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read."""
        result = await self._session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.user_id == user_id)
            .values(is_read=True)
        )
        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read."""
        result = await self._session.execute(
            update(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
            .values(is_read=True)
        )
        return result.rowcount

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get unread notification count."""
        result = await self._session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
        return result.scalar_one()

    async def create_delivery_plan(
        self,
        signal_id: UUID,
        subscription_id: UUID,
        user_id: UUID,
        channel: DeliveryChannel,
        payload: dict,
        scheduled_at: datetime | None = None,
    ) -> DeliveryPlan:
        """Create a delivery plan for a signal."""
        plan = DeliveryPlan(
            signal_id=signal_id,
            subscription_id=subscription_id,
            user_id=user_id,
            channel=channel,
            payload=payload,
            scheduled_at=scheduled_at,
            status=DeliveryStatus.PENDING,
        )
        self._session.add(plan)
        await self._session.flush()
        await self._session.refresh(plan)
        return plan

    async def get_pending_deliveries(
        self,
        limit: int = 100,
    ) -> list[DeliveryPlan]:
        """Get pending delivery plans."""
        result = await self._session.execute(
            select(DeliveryPlan)
            .where(DeliveryPlan.status == DeliveryStatus.PENDING)
            .where(
                (DeliveryPlan.scheduled_at.is_(None)) |
                (DeliveryPlan.scheduled_at <= datetime.utcnow())
            )
            .order_by(DeliveryPlan.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_delivery_status(
        self,
        delivery_id: UUID,
        status: DeliveryStatus,
        error_message: str | None = None,
    ) -> None:
        """Update delivery plan status."""
        values = {"status": status}
        if status == DeliveryStatus.SENT:
            values["sent_at"] = datetime.utcnow()
        if error_message:
            values["error_message"] = error_message
            values["retry_count"] = DeliveryPlan.retry_count + 1

        await self._session.execute(
            update(DeliveryPlan)
            .where(DeliveryPlan.id == delivery_id)
            .values(**values)
        )
