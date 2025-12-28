"""Subscription service."""

from datetime import datetime
from uuid import UUID

from src.infra.database.repositories.subscription_repo import SubscriptionRepository
from src.infra.database.repositories.strategy_repo import StrategyRepository
from src.infra.database.repositories.user_repo import UserRepository
from src.infra.database.models import Subscription
from src.domain.entities.subscription import SubscriptionEntity
from src.core.constants import SubscriptionStatus, DeliveryChannel, SUBSCRIPTION_LIMITS
from src.core.exceptions import (
    StrategyNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionLimitExceededError,
    DuplicateSubscriptionError,
    InvalidParamsError,
    StrategyInactiveError,
    PermissionDeniedError,
)


class SubscriptionService:
    """Service for subscription operations."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        strategy_repo: StrategyRepository,
        user_repo: UserRepository,
    ):
        self._sub_repo = subscription_repo
        self._strategy_repo = strategy_repo
        self._user_repo = user_repo

    async def create_subscription(
        self,
        user_id: UUID,
        strategy_id: str,
        params: dict | None = None,
        channels: list[str] | None = None,
        cooldown_seconds: int | None = None,
    ) -> SubscriptionEntity:
        """Create a new subscription."""
        # Check strategy exists and is active
        strategy = await self._strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise StrategyNotFoundError(strategy_id)
        if not strategy.is_active:
            raise StrategyInactiveError(strategy_id)

        # Check user tier
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise PermissionDeniedError("subscribe")

        user_entity = self._user_repo.to_entity(user)
        if not user_entity.can_subscribe_to_strategy(strategy.tier_required):
            raise PermissionDeniedError(f"subscribe to this strategy (requires {strategy.tier_required.value} tier)")

        # Check subscription limit
        sub_count = await self._sub_repo.count_by_user(user_id)
        limit = SUBSCRIPTION_LIMITS.get(user.tier, 5)
        if sub_count >= limit:
            raise SubscriptionLimitExceededError()

        # Check duplicate
        existing = await self._sub_repo.get_by_user_and_strategy(user_id, strategy_id)
        if existing and existing.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED):
            raise DuplicateSubscriptionError(strategy_id)

        # Validate params
        strategy_entity = self._strategy_repo.to_entity(strategy)
        merged_params = strategy_entity.merge_params(params or {})
        is_valid, errors = strategy_entity.validate_params(merged_params)
        if not is_valid:
            raise InvalidParamsError(errors)

        # Create subscription
        subscription = Subscription(
            user_id=user_id,
            strategy_id=strategy_id,
            params=merged_params,
            channels=channels or [DeliveryChannel.SITE.value],
            cooldown_seconds=cooldown_seconds or strategy.default_cooldown,
            status=SubscriptionStatus.ACTIVE,
        )

        saved = await self._sub_repo.create(subscription)
        return self._sub_repo.to_entity(saved)

    async def get_user_subscriptions(
        self,
        user_id: UUID,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SubscriptionEntity]:
        """Get user's subscriptions."""
        if active_only:
            subs = await self._sub_repo.get_active_by_user(user_id, skip, limit)
        else:
            subs = await self._sub_repo.get_by_user(user_id, skip, limit)

        return [self._sub_repo.to_entity(s) for s in subs]

    async def get_by_id(self, subscription_id: UUID, user_id: UUID) -> SubscriptionEntity:
        """Get subscription by ID."""
        sub = await self._sub_repo.get_by_id(subscription_id)
        if not sub or sub.user_id != user_id:
            raise SubscriptionNotFoundError(str(subscription_id))
        return self._sub_repo.to_entity(sub)

    async def update_subscription(
        self,
        subscription_id: UUID,
        user_id: UUID,
        params: dict | None = None,
        channels: list[str] | None = None,
        cooldown_seconds: int | None = None,
    ) -> SubscriptionEntity:
        """Update subscription settings."""
        sub = await self._sub_repo.get_by_id(subscription_id)
        if not sub or sub.user_id != user_id:
            raise SubscriptionNotFoundError(str(subscription_id))

        if params is not None:
            strategy = await self._strategy_repo.get_by_id(sub.strategy_id)
            if strategy:
                strategy_entity = self._strategy_repo.to_entity(strategy)
                merged_params = strategy_entity.merge_params(params)
                is_valid, errors = strategy_entity.validate_params(merged_params)
                if not is_valid:
                    raise InvalidParamsError(errors)
                sub.params = merged_params

        if channels is not None:
            sub.channels = channels

        if cooldown_seconds is not None:
            sub.cooldown_seconds = cooldown_seconds

        sub.updated_at = datetime.utcnow()
        updated = await self._sub_repo.update(sub)
        return self._sub_repo.to_entity(updated)

    async def pause(self, subscription_id: UUID, user_id: UUID) -> SubscriptionEntity:
        """Pause a subscription."""
        sub = await self._sub_repo.get_by_id(subscription_id)
        if not sub or sub.user_id != user_id:
            raise SubscriptionNotFoundError(str(subscription_id))

        await self._sub_repo.update_status(subscription_id, SubscriptionStatus.PAUSED)
        sub.status = SubscriptionStatus.PAUSED
        return self._sub_repo.to_entity(sub)

    async def resume(self, subscription_id: UUID, user_id: UUID) -> SubscriptionEntity:
        """Resume a subscription."""
        sub = await self._sub_repo.get_by_id(subscription_id)
        if not sub or sub.user_id != user_id:
            raise SubscriptionNotFoundError(str(subscription_id))

        await self._sub_repo.update_status(subscription_id, SubscriptionStatus.ACTIVE)
        sub.status = SubscriptionStatus.ACTIVE
        return self._sub_repo.to_entity(sub)

    async def cancel(self, subscription_id: UUID, user_id: UUID) -> bool:
        """Cancel a subscription."""
        sub = await self._sub_repo.get_by_id(subscription_id)
        if not sub or sub.user_id != user_id:
            raise SubscriptionNotFoundError(str(subscription_id))

        await self._sub_repo.update_status(subscription_id, SubscriptionStatus.CANCELLED)
        return True
