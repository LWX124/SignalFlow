"""Instrument endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_optional_user
from src.infra.database import get_db
from src.infra.database.models import Instrument
from src.domain.entities.user import UserEntity

router = APIRouter(prefix="/instruments")


class InstrumentResponse(BaseModel):
    id: str
    symbol: str
    name: str
    market: str
    type: str
    exchange: str | None
    currency: str
    is_active: bool


class InstrumentsListResponse(BaseModel):
    items: list[InstrumentResponse]
    total: int


@router.get("", response_model=InstrumentsListResponse)
async def list_instruments(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserEntity | None, Depends(get_optional_user)],
    market: str | None = None,
    type: str | None = None,
    q: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List instruments with filters."""
    query = select(Instrument).where(Instrument.is_active == True)

    if market:
        query = query.where(Instrument.market == market)
    if type:
        query = query.where(Instrument.type == type)
    if q:
        query = query.where(
            Instrument.symbol.ilike(f"%{q}%") | Instrument.name.ilike(f"%{q}%")
        )

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    instruments = list(result.scalars().all())

    return InstrumentsListResponse(
        items=[
            InstrumentResponse(
                id=str(i.id),
                symbol=i.symbol,
                name=i.name,
                market=i.market.value,
                type=i.type.value,
                exchange=i.exchange,
                currency=i.currency,
                is_active=i.is_active,
            )
            for i in instruments
        ],
        total=len(instruments),
    )


@router.get("/{symbol}", response_model=InstrumentResponse)
async def get_instrument(
    symbol: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    market: str | None = None,
):
    """Get instrument by symbol."""
    query = select(Instrument).where(Instrument.symbol == symbol)
    if market:
        query = query.where(Instrument.market == market)

    result = await session.execute(query)
    instrument = result.scalar_one_or_none()

    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument '{symbol}' not found",
        )

    return InstrumentResponse(
        id=str(instrument.id),
        symbol=instrument.symbol,
        name=instrument.name,
        market=instrument.market.value,
        type=instrument.type.value,
        exchange=instrument.exchange,
        currency=instrument.currency,
        is_active=instrument.is_active,
    )


@router.get("/{symbol}/signals")
async def get_instrument_signals(
    symbol: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserEntity | None, Depends(get_optional_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get signals related to an instrument."""
    from src.infra.database.models import Signal

    result = await session.execute(
        select(Signal)
        .where(Signal.symbol == symbol)
        .order_by(Signal.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    signals = list(result.scalars().all())

    return {
        "items": [
            {
                "id": str(s.id),
                "strategy_id": s.strategy_id,
                "side": s.side.value,
                "confidence": float(s.confidence),
                "reason_points": s.reason_points,
                "created_at": s.created_at.isoformat(),
            }
            for s in signals
        ],
        "total": len(signals),
    }
