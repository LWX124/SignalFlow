"""Strategy repository."""

from sqlalchemy import select, update

from src.infra.database.models import Strategy
from src.infra.database.repositories.base import BaseRepository
from src.domain.entities.strategy import StrategyEntity
from src.core.constants import StrategyType, UserTier


class StrategyRepository(BaseRepository[Strategy]):
    """Repository for Strategy model."""

    model = Strategy

    async def get_active_strategies(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Strategy]:
        """Get all active strategies."""
        result = await self._session.execute(
            select(Strategy)
            .where(Strategy.is_active == True)
            .where(Strategy.is_public == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_type(
        self,
        strategy_type: StrategyType,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Strategy]:
        """Get strategies by type."""
        result = await self._session.execute(
            select(Strategy)
            .where(Strategy.type == strategy_type)
            .where(Strategy.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_market(
        self,
        market: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Strategy]:
        """Get strategies by market."""
        result = await self._session.execute(
            select(Strategy)
            .where(Strategy.markets.contains([market]))
            .where(Strategy.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_tier(
        self,
        tier: UserTier,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Strategy]:
        """Get strategies available for a specific tier."""
        tier_order = {UserTier.FREE: 0, UserTier.PRO: 1, UserTier.ENTERPRISE: 2}
        user_tier_level = tier_order[tier]

        # Get strategies where tier_required <= user's tier
        result = await self._session.execute(
            select(Strategy)
            .where(Strategy.is_active == True)
            .where(Strategy.is_public == True)
            .offset(skip)
            .limit(limit)
        )

        strategies = list(result.scalars().all())
        # Filter by tier level
        return [
            s for s in strategies
            if tier_order.get(s.tier_required, 0) <= user_tier_level
        ]

    async def update_metrics(
        self,
        strategy_id: str,
        metrics: dict,
    ) -> None:
        """Update strategy metrics summary."""
        await self._session.execute(
            update(Strategy)
            .where(Strategy.id == strategy_id)
            .values(metrics_summary=metrics)
        )

    async def activate(self, strategy_id: str) -> None:
        """Activate a strategy."""
        await self._session.execute(
            update(Strategy)
            .where(Strategy.id == strategy_id)
            .values(is_active=True)
        )

    async def deactivate(self, strategy_id: str) -> None:
        """Deactivate a strategy."""
        await self._session.execute(
            update(Strategy)
            .where(Strategy.id == strategy_id)
            .values(is_active=False)
        )

    def to_entity(self, model: Strategy) -> StrategyEntity:
        """Convert model to entity."""
        return StrategyEntity(
            id=model.id,
            version=model.version,
            name=model.name,
            description=model.description,
            type=model.type,
            markets=model.markets,
            risk_level=model.risk_level,
            frequency_hint=model.frequency_hint,
            params_schema=model.params_schema,
            default_params=model.default_params,
            default_cooldown=model.default_cooldown,
            metrics_summary=model.metrics_summary,
            is_active=model.is_active,
            is_public=model.is_public,
            tier_required=model.tier_required,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
