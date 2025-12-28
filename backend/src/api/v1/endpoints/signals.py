"""Signal endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.api.deps import get_current_user, get_signal_service
from src.services.signal_service import SignalService
from src.domain.entities.user import UserEntity

router = APIRouter(prefix="/signals")


class SignalResponse(BaseModel):
    id: str
    strategy_id: str
    strategy_version: str
    symbol: str
    market: str
    side: str
    confidence: float
    reason_points: list[str]
    risk_tags: list[str]
    snapshot: dict
    created_at: str | None


class SignalDetailResponse(SignalResponse):
    ai_explain: str | None


class SignalsListResponse(BaseModel):
    items: list[SignalResponse]
    next_cursor: str | None
    has_more: bool


def to_response(entity) -> SignalResponse:
    return SignalResponse(
        id=str(entity.id) if entity.id else "",
        strategy_id=entity.strategy_id,
        strategy_version=entity.strategy_version,
        symbol=entity.symbol,
        market=entity.market.value if hasattr(entity.market, 'value') else entity.market,
        side=entity.side.value if hasattr(entity.side, 'value') else entity.side,
        confidence=entity.confidence,
        reason_points=entity.reason_points,
        risk_tags=entity.risk_tags,
        snapshot=entity.snapshot,
        created_at=entity.created_at.isoformat() if entity.created_at else None,
    )


@router.get("", response_model=SignalsListResponse)
async def list_signals(
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    signal_service: Annotated[SignalService, Depends(get_signal_service)],
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    strategy_id: str | None = None,
    symbol: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
):
    """List signals for user's subscribed strategies."""
    result = await signal_service.list_user_signals(
        user_id=current_user.id,
        strategy_id=strategy_id,
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        cursor=cursor,
        limit=limit,
    )

    return SignalsListResponse(
        items=[to_response(s) for s in result.items],
        next_cursor=result.next_cursor,
        has_more=result.has_more,
    )


@router.get("/{signal_id}", response_model=SignalDetailResponse)
async def get_signal_detail(
    signal_id: UUID,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    signal_service: Annotated[SignalService, Depends(get_signal_service)],
):
    """Get signal details with AI explanation."""
    detail = await signal_service.get_signal_detail(signal_id, current_user.id)

    return SignalDetailResponse(
        id=str(detail.get("id", "")),
        strategy_id=detail.get("strategy_id", ""),
        strategy_version=detail.get("strategy_version", ""),
        symbol=detail.get("symbol", ""),
        market=detail.get("market", ""),
        side=detail.get("side", ""),
        confidence=detail.get("confidence", 0),
        reason_points=detail.get("reason_points", []),
        risk_tags=detail.get("risk_tags", []),
        snapshot=detail.get("snapshot", {}),
        created_at=detail.get("created_at"),
        ai_explain=detail.get("ai_explain"),
    )
