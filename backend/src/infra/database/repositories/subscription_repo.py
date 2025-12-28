"""Subscription repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, func, and_

from src.infra.database.models import Subscription
from src.infra.database.repositories.base import BaseRepository
from src.domain.entities.subscription import SubscriptionEntity
from src.core.constants import SubscriptionStatus


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository for Subscription model."""

    model = Subscription

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Subscription]:
        """Get subscriptions for a user."""
        result = await self._session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Subscription]:
        """Get active subscriptions for a user."""
        result = await self._session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .order_by(Subscription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_strategy(
        self,
        strategy_id: str,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Subscription]:
        """Get subscriptions for a strategy."""
        query = select(Subscription).where(Subscription.strategy_id == strategy_id)

        if active_only:
            query = query.where(Subscription.status == SubscriptionStatus.ACTIVE)

        result = await self._session.execute(
            query.order_by(Subscription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user_and_strategy(
        self,
        user_id: UUID,
        strategy_id: str,
    ) -> Subscription | None:
        """Get subscription by user and strategy."""
        result = await self._session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.strategy_id == strategy_id)
        )
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: UUID) -> int:
        """Count subscriptions for a user."""
        result = await self._session.execute(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.PAUSED,
            ]))
        )
        return result.scalar_one()

    async def count_active_by_strategy(self, strategy_id: str) -> int:
        """Count active subscriptions for a strategy."""
        result = await self._session.execute(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.strategy_id == strategy_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
        )
        return result.scalar_one()

    async def update_status(
        self,
        subscription_id: UUID,
        status: SubscriptionStatus,
    ) -> None:
        """Update subscription status."""
        await self._session.execute(
            update(Subscription)
            .where(Subscription.id == subscription_id)
            .values(status=status, updated_at=datetime.utcnow())
        )

    async def record_signal(
        self,
        subscription_id: UUID,
        signal_time: datetime | None = None,
    ) -> None:
        """Record that a signal was sent to this subscription."""
        await self._session.execute(
            update(Subscription)
            .where(Subscription.id == subscription_id)
            .values(
                last_signal_at=signal_time or datetime.utcnow(),
                signal_count=Subscription.signal_count + 1,
                updated_at=datetime.utcnow(),
            )
        )

    async def get_eligible_subscriptions(
        self,
        strategy_id: str,
        cooldown_cutoff: datetime,
    ) -> list[Subscription]:
        """
        Get subscriptions eligible to receive a signal.

        Eligible = active status AND (never received OR last_signal_at < cooldown_cutoff)
        """
        result = await self._session.execute(
            select(Subscription)
            .where(Subscription.strategy_id == strategy_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .where(
                and_(
                    Subscription.last_signal_at.is_(None)
                ) | (
                    Subscription.last_signal_at < cooldown_cutoff
                )
            )
        )
        return list(result.scalars().all())

    def to_entity(self, model: Subscription) -> SubscriptionEntity:
        """Convert model to entity."""
        return SubscriptionEntity(
            id=model.id,
            user_id=model.user_id,
            strategy_id=model.strategy_id,
            params=model.params,
            channels=model.channels,
            cooldown_seconds=model.cooldown_seconds,
            status=model.status,
            last_signal_at=model.last_signal_at,
            signal_count=model.signal_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
