"""Strategy endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.api.deps import get_strategy_service, get_optional_user
from src.services.strategy_service import StrategyService
from src.domain.entities.user import UserEntity
from src.core.constants import StrategyType

router = APIRouter(prefix="/strategies")


class StrategyResponse(BaseModel):
    id: str
    version: str
    name: str
    description: str | None
    type: str
    markets: list[str]
    risk_level: str | None
    frequency_hint: str | None
    params_schema: dict
    default_params: dict
    default_cooldown: int
    metrics_summary: dict
    tier_required: str


class StrategiesListResponse(BaseModel):
    items: list[StrategyResponse]
    total: int


@router.get("", response_model=StrategiesListResponse)
async def list_strategies(
    strategy_service: Annotated[StrategyService, Depends(get_strategy_service)],
    current_user: Annotated[UserEntity | None, Depends(get_optional_user)],
    type: StrategyType | None = None,
    market: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List available strategies."""
    user_tier = current_user.tier if current_user else None

    strategies = await strategy_service.list_strategies(
        skip=skip,
        limit=limit,
        strategy_type=type,
        market=market,
        user_tier=user_tier,
    )

    return StrategiesListResponse(
        items=[
            StrategyResponse(
                id=s.id,
                version=s.version,
                name=s.name,
                description=s.description,
                type=s.type.value,
                markets=s.markets,
                risk_level=s.risk_level.value if s.risk_level else None,
                frequency_hint=s.frequency_hint,
                params_schema=s.params_schema,
                default_params=s.default_params,
                default_cooldown=s.default_cooldown,
                metrics_summary=s.metrics_summary,
                tier_required=s.tier_required.value,
            )
            for s in strategies
        ],
        total=len(strategies),
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    strategy_service: Annotated[StrategyService, Depends(get_strategy_service)],
):
    """Get strategy details."""
    strategy = await strategy_service.get_by_id(strategy_id)

    return StrategyResponse(
        id=strategy.id,
        version=strategy.version,
        name=strategy.name,
        description=strategy.description,
        type=strategy.type.value,
        markets=strategy.markets,
        risk_level=strategy.risk_level.value if strategy.risk_level else None,
        frequency_hint=strategy.frequency_hint,
        params_schema=strategy.params_schema,
        default_params=strategy.default_params,
        default_cooldown=strategy.default_cooldown,
        metrics_summary=strategy.metrics_summary,
        tier_required=strategy.tier_required.value,
    )


@router.get("/{strategy_id}/signals")
async def get_strategy_signals(
    strategy_id: str,
    strategy_service: Annotated[StrategyService, Depends(get_strategy_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get historical signals for a strategy."""
    from src.infra.database.connection import get_session
    from src.infra.database.repositories.signal_repo import SignalRepository

    # Verify strategy exists
    await strategy_service.get_by_id(strategy_id)

    async with get_session() as session:
        repo = SignalRepository(session)
        signals = await repo.get_by_strategy(strategy_id, skip=skip, limit=limit)

        return {
            "items": [
                {
                    "id": str(s.id),
                    "symbol": s.symbol,
                    "market": s.market.value,
                    "side": s.side.value,
                    "confidence": float(s.confidence),
                    "reason_points": s.reason_points,
                    "risk_tags": s.risk_tags,
                    "created_at": s.created_at.isoformat(),
                }
                for s in signals
            ],
            "total": len(signals),
        }


@router.get("/{strategy_id}/performance")
async def get_strategy_performance(
    strategy_id: str,
    strategy_service: Annotated[StrategyService, Depends(get_strategy_service)],
    days: int = Query(30, ge=1, le=365),
):
    """Get performance statistics for a strategy."""
    from datetime import datetime, timedelta
    from src.infra.database.connection import get_session
    from src.infra.database.repositories.signal_repo import SignalRepository

    # Verify strategy exists
    strategy = await strategy_service.get_by_id(strategy_id)

    async with get_session() as session:
        repo = SignalRepository(session)
        since = datetime.utcnow() - timedelta(days=days)
        signal_count = await repo.count_by_strategy_since(strategy_id, since)

        # Return metrics from strategy + computed count
        return {
            "strategy_id": strategy_id,
            "period_days": days,
            "signal_count": signal_count,
            "metrics_summary": strategy.metrics_summary,
        }
