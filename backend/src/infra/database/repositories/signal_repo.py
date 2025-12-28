"""Signal repository."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, func, and_

from src.infra.database.models import Signal, SignalExplain
from src.infra.database.repositories.base import BaseRepository
from src.domain.entities.signal import SignalEntity
from src.domain.value_objects.pagination import CursorPagination, PagedResult
from src.core.constants import Market, SignalSide


class SignalRepository(BaseRepository[Signal]):
    """Repository for Signal model."""

    model = Signal

    async def get_by_strategy(
        self,
        strategy_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Signal]:
        """Get signals for a strategy."""
        result = await self._session.execute(
            select(Signal)
            .where(Signal.strategy_id == strategy_id)
            .order_by(Signal.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_symbol(
        self,
        symbol: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Signal]:
        """Get signals for a symbol."""
        result = await self._session.execute(
            select(Signal)
            .where(Signal.symbol == symbol)
            .order_by(Signal.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_filters(
        self,
        strategy_ids: list[str] | None = None,
        symbol: str | None = None,
        market: Market | None = None,
        side: SignalSide | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        pagination: CursorPagination | None = None,
    ) -> PagedResult[Signal]:
        """Get signals with filters and cursor pagination."""
        query = select(Signal)

        # Apply filters
        conditions = []

        if strategy_ids:
            conditions.append(Signal.strategy_id.in_(strategy_ids))

        if symbol:
            conditions.append(Signal.symbol == symbol)

        if market:
            conditions.append(Signal.market == market)

        if side:
            conditions.append(Signal.side == side)

        if start_time:
            conditions.append(Signal.created_at >= start_time)

        if end_time:
            conditions.append(Signal.created_at <= end_time)

        if conditions:
            query = query.where(and_(*conditions))

        # Apply cursor pagination
        if pagination:
            cursor_data = pagination.decode_cursor()
            if cursor_data:
                cursor_time = datetime.fromisoformat(cursor_data["created_at"])
                cursor_id = UUID(cursor_data["id"])
                query = query.where(
                    and_(
                        Signal.created_at <= cursor_time,
                        Signal.id < cursor_id,
                    ) | (Signal.created_at < cursor_time)
                )

            limit = pagination.limit
        else:
            limit = 20

        # Order by created_at desc, id desc
        query = query.order_by(Signal.created_at.desc(), Signal.id.desc())

        # Fetch one more to check if there are more results
        query = query.limit(limit + 1)

        result = await self._session.execute(query)
        signals = list(result.scalars().all())

        # Check if there are more results
        has_more = len(signals) > limit
        if has_more:
            signals = signals[:limit]

        # Generate next cursor
        next_cursor = None
        if has_more and signals:
            last_signal = signals[-1]
            next_cursor = CursorPagination.encode_cursor({
                "created_at": last_signal.created_at.isoformat(),
                "id": str(last_signal.id),
            })

        return PagedResult(
            items=signals,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def get_recent_by_dedup_key(
        self,
        dedup_key: str,
        since: datetime,
    ) -> Signal | None:
        """Get the most recent signal with the given dedup key since a time."""
        result = await self._session.execute(
            select(Signal)
            .where(Signal.dedup_key == dedup_key)
            .where(Signal.created_at >= since)
            .order_by(Signal.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_strategy_since(
        self,
        strategy_id: str,
        since: datetime,
    ) -> int:
        """Count signals for a strategy since a time."""
        result = await self._session.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.strategy_id == strategy_id)
            .where(Signal.created_at >= since)
        )
        return result.scalar_one()

    async def get_with_explain(self, signal_id: UUID) -> tuple[Signal | None, SignalExplain | None]:
        """Get signal with its AI explanation."""
        signal_result = await self._session.execute(
            select(Signal).where(Signal.id == signal_id)
        )
        signal = signal_result.scalar_one_or_none()

        if not signal:
            return None, None

        explain_result = await self._session.execute(
            select(SignalExplain).where(SignalExplain.signal_id == signal_id)
        )
        explain = explain_result.scalar_one_or_none()

        return signal, explain

    async def add_explain(
        self,
        signal_id: UUID,
        content: str,
        model: str | None = None,
        prompt_version: str | None = None,
    ) -> SignalExplain:
        """Add AI explanation to a signal."""
        explain = SignalExplain(
            signal_id=signal_id,
            content=content,
            model=model,
            prompt_version=prompt_version,
        )
        self._session.add(explain)
        await self._session.flush()
        await self._session.refresh(explain)
        return explain

    def to_entity(self, model: Signal) -> SignalEntity:
        """Convert model to entity."""
        return SignalEntity(
            id=model.id,
            strategy_id=model.strategy_id,
            strategy_version=model.strategy_version,
            symbol=model.symbol,
            market=model.market,
            side=model.side,
            confidence=float(model.confidence),
            reason_points=model.reason_points if isinstance(model.reason_points, list) else model.reason_points.get("points", []),
            risk_tags=model.risk_tags,
            snapshot=model.snapshot,
            dedup_key=model.dedup_key,
            created_at=model.created_at,
        )
