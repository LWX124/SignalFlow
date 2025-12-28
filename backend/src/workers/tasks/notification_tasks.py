"""Notification delivery tasks."""

import asyncio
from datetime import datetime
from uuid import UUID

from src.workers.celery_app import celery_app
from src.core.logging import get_logger
from src.core.constants import DeliveryStatus, DeliveryChannel

logger = get_logger(__name__)


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task
def process_pending_deliveries():
    """Process pending delivery plans."""
    logger.info("Processing pending deliveries")

    async def _process():
        from src.infra.database.connection import get_session
        from src.services.notification_service import NotificationService

        async with get_session() as session:
            service = NotificationService(session)
            pending = await service.get_pending_deliveries(limit=100)

            processed = 0
            for plan in pending:
                try:
                    # Dispatch to appropriate channel
                    if plan.channel == DeliveryChannel.SITE:
                        await deliver_site_notification.delay(str(plan.id))
                    elif plan.channel == DeliveryChannel.EMAIL:
                        await deliver_email.delay(str(plan.id))
                    elif plan.channel == DeliveryChannel.WECHAT:
                        await deliver_wechat.delay(str(plan.id))

                    processed += 1
                except Exception as e:
                    logger.error("Failed to dispatch delivery", plan_id=str(plan.id), error=str(e))

            return {"processed": processed}

    return run_async(_process())


@celery_app.task(bind=True, max_retries=3)
def deliver_site_notification(self, delivery_id: str):
    """Deliver in-app notification."""
    logger.info("Delivering site notification", delivery_id=delivery_id)

    async def _deliver():
        from src.infra.database.connection import get_session
        from src.services.notification_service import NotificationService
        from src.core.constants import NotificationType

        async with get_session() as session:
            service = NotificationService(session)

            # Get delivery plan
            from sqlalchemy import select
            from src.infra.database.models import DeliveryPlan

            result = await session.execute(
                select(DeliveryPlan).where(DeliveryPlan.id == UUID(delivery_id))
            )
            plan = result.scalar_one_or_none()

            if not plan:
                return {"status": "error", "message": "Delivery plan not found"}

            # Create notification
            payload = plan.payload
            await service.create_notification(
                user_id=plan.user_id,
                notification_type=NotificationType.SIGNAL,
                title=payload.get("title", "New Signal"),
                content=payload.get("content"),
                link=payload.get("link"),
                metadata=payload.get("metadata", {}),
            )

            # Update delivery status
            await service.update_delivery_status(plan.id, DeliveryStatus.SENT)

            return {"status": "success", "delivery_id": delivery_id}

    try:
        return run_async(_deliver())
    except Exception as exc:
        logger.error("Site notification delivery failed", delivery_id=delivery_id, error=str(exc))
        self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, max_retries=3)
def deliver_email(self, delivery_id: str):
    """Deliver email notification."""
    logger.info("Delivering email", delivery_id=delivery_id)
    # TODO: Implement email delivery
    return {"status": "not_implemented", "delivery_id": delivery_id}


@celery_app.task(bind=True, max_retries=3)
def deliver_wechat(self, delivery_id: str):
    """Deliver WeChat notification."""
    logger.info("Delivering WeChat notification", delivery_id=delivery_id)
    # TODO: Implement WeChat delivery
    return {"status": "not_implemented", "delivery_id": delivery_id}


@celery_app.task
def send_signal_notifications(signal_id: str, strategy_id: str):
    """Create delivery plans for a new signal."""
    logger.info("Creating signal notifications", signal_id=signal_id, strategy_id=strategy_id)

    async def _create():
        from src.infra.database.connection import get_session
        from src.infra.database.repositories.subscription_repo import SubscriptionRepository
        from src.services.notification_service import NotificationService
        from datetime import timedelta

        async with get_session() as session:
            sub_repo = SubscriptionRepository(session)
            notification_service = NotificationService(session)

            # Get eligible subscriptions
            cooldown_cutoff = datetime.utcnow() - timedelta(hours=1)
            subs = await sub_repo.get_eligible_subscriptions(strategy_id, cooldown_cutoff)

            created = 0
            for sub in subs:
                for channel in sub.channels:
                    try:
                        await notification_service.create_delivery_plan(
                            signal_id=UUID(signal_id),
                            subscription_id=sub.id,
                            user_id=sub.user_id,
                            channel=DeliveryChannel(channel),
                            payload={
                                "title": f"New Signal from {strategy_id}",
                                "content": "A new trading signal has been generated.",
                                "link": f"/signals/{signal_id}",
                            },
                        )
                        created += 1
                    except Exception as e:
                        logger.error("Failed to create delivery plan", error=str(e))

            return {"created": created, "signal_id": signal_id}

    return run_async(_create())
