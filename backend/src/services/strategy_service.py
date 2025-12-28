"""Strategy service."""

from typing import Any

from src.infra.database.repositories.strategy_repo import StrategyRepository
from src.infra.database.models import Strategy
from src.domain.entities.strategy import StrategyEntity
from src.core.constants import StrategyType, UserTier
from src.core.exceptions import StrategyNotFoundError


class StrategyService:
    """Service for strategy operations."""

    def __init__(self, strategy_repo: StrategyRepository):
        self._repo = strategy_repo

    async def get_by_id(self, strategy_id: str) -> StrategyEntity:
        """Get strategy by ID."""
        strategy = await self._repo.get_by_id(strategy_id)
        if not strategy:
            raise StrategyNotFoundError(strategy_id)
        return self._repo.to_entity(strategy)

    async def list_strategies(
        self,
        skip: int = 0,
        limit: int = 100,
        strategy_type: StrategyType | None = None,
        market: str | None = None,
        user_tier: UserTier | None = None,
    ) -> list[StrategyEntity]:
        """List strategies with filters."""
        if strategy_type:
            strategies = await self._repo.get_by_type(strategy_type, skip, limit)
        elif market:
            strategies = await self._repo.get_by_market(market, skip, limit)
        elif user_tier:
            strategies = await self._repo.get_by_tier(user_tier, skip, limit)
        else:
            strategies = await self._repo.get_active_strategies(skip, limit)

        return [self._repo.to_entity(s) for s in strategies]

    async def create_strategy(
        self,
        strategy_id: str,
        name: str,
        strategy_type: StrategyType,
        params_schema: dict[str, Any],
        **kwargs,
    ) -> StrategyEntity:
        """Create a new strategy."""
        strategy = Strategy(
            id=strategy_id,
            version=kwargs.get("version", "1.0.0"),
            name=name,
            description=kwargs.get("description"),
            type=strategy_type,
            markets=kwargs.get("markets", []),
            risk_level=kwargs.get("risk_level"),
            frequency_hint=kwargs.get("frequency_hint"),
            params_schema=params_schema,
            default_params=kwargs.get("default_params", {}),
            default_cooldown=kwargs.get("default_cooldown", 3600),
            is_active=True,
            is_public=kwargs.get("is_public", True),
            tier_required=kwargs.get("tier_required", UserTier.FREE),
        )

        saved = await self._repo.create(strategy)
        return self._repo.to_entity(saved)

    async def update_metrics(
        self,
        strategy_id: str,
        metrics: dict[str, Any],
    ) -> None:
        """Update strategy metrics."""
        strategy = await self._repo.get_by_id(strategy_id)
        if not strategy:
            raise StrategyNotFoundError(strategy_id)

        await self._repo.update_metrics(strategy_id, metrics)

    async def activate(self, strategy_id: str) -> None:
        """Activate a strategy."""
        strategy = await self._repo.get_by_id(strategy_id)
        if not strategy:
            raise StrategyNotFoundError(strategy_id)
        await self._repo.activate(strategy_id)

    async def deactivate(self, strategy_id: str) -> None:
        """Deactivate a strategy."""
        strategy = await self._repo.get_by_id(strategy_id)
        if not strategy:
            raise StrategyNotFoundError(strategy_id)
        await self._repo.deactivate(strategy_id)
