"""Signal service."""

from datetime import datetime, timedelta
from uuid import UUID

from src.infra.database.repositories.signal_repo import SignalRepository
from src.infra.database.repositories.subscription_repo import SubscriptionRepository
from src.infra.database.models import Signal
from src.domain.entities.signal import SignalEntity
from src.domain.value_objects.pagination import CursorPagination, PagedResult
from src.core.constants import Market, SignalSide
from src.core.exceptions import SignalNotFoundError


class SignalService:
    """Service for signal operations."""

    def __init__(
        self,
        signal_repo: SignalRepository,
        subscription_repo: SubscriptionRepository,
    ):
        self._signal_repo = signal_repo
        self._sub_repo = subscription_repo

    async def get_by_id(self, signal_id: UUID) -> SignalEntity:
        """Get signal by ID."""
        signal = await self._signal_repo.get_by_id(signal_id)
        if not signal:
            raise SignalNotFoundError(str(signal_id))
        return self._signal_repo.to_entity(signal)

    async def get_signal_detail(self, signal_id: UUID, user_id: UUID) -> dict:
        """Get signal detail with AI explanation."""
        signal, explain = await self._signal_repo.get_with_explain(signal_id)
        if not signal:
            raise SignalNotFoundError(str(signal_id))

        entity = self._signal_repo.to_entity(signal)
        result = entity.to_dict()
        result["ai_explain"] = explain.content if explain else None

        return result

    async def list_user_signals(
        self,
        user_id: UUID,
        strategy_id: str | None = None,
        symbol: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> PagedResult[SignalEntity]:
        """List signals for user's subscribed strategies."""
        # Get user's subscribed strategy IDs
        subs = await self._sub_repo.get_by_user(user_id)
        strategy_ids = [s.strategy_id for s in subs]

        if not strategy_ids:
            return PagedResult(items=[], has_more=False)

        # Filter by specific strategy if provided
        if strategy_id:
            if strategy_id not in strategy_ids:
                return PagedResult(items=[], has_more=False)
            strategy_ids = [strategy_id]

        pagination = CursorPagination(cursor=cursor, limit=limit)

        result = await self._signal_repo.get_with_filters(
            strategy_ids=strategy_ids,
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            pagination=pagination,
        )

        return PagedResult(
            items=[self._signal_repo.to_entity(s) for s in result.items],
            next_cursor=result.next_cursor,
            has_more=result.has_more,
        )

    async def create_signal(
        self,
        strategy_id: str,
        strategy_version: str,
        symbol: str,
        market: Market,
        side: SignalSide,
        confidence: float,
        reason_points: list[str],
        snapshot: dict,
        risk_tags: list[str] | None = None,
        dedup_key: str | None = None,
    ) -> SignalEntity:
        """Create a new signal."""
        signal = Signal(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            symbol=symbol,
            market=market,
            side=side,
            confidence=confidence,
            reason_points=reason_points,
            risk_tags=risk_tags or [],
            snapshot=snapshot,
            dedup_key=dedup_key,
        )

        saved = await self._signal_repo.create(signal)
        return self._signal_repo.to_entity(saved)

    async def check_duplicate(
        self,
        dedup_key: str,
        cooldown_seconds: int,
    ) -> bool:
        """Check if a signal with the same dedup key exists within cooldown."""
        since = datetime.utcnow() - timedelta(seconds=cooldown_seconds)
        existing = await self._signal_repo.get_recent_by_dedup_key(dedup_key, since)
        return existing is not None

    async def add_explanation(
        self,
        signal_id: UUID,
        content: str,
        model: str | None = None,
    ) -> None:
        """Add AI explanation to a signal."""
        signal = await self._signal_repo.get_by_id(signal_id)
        if not signal:
            raise SignalNotFoundError(str(signal_id))

        await self._signal_repo.add_explain(signal_id, content, model)

    async def get_strategy_signal_count(
        self,
        strategy_id: str,
        days: int = 30,
    ) -> int:
        """Get signal count for a strategy in the last N days."""
        since = datetime.utcnow() - timedelta(days=days)
        return await self._signal_repo.count_by_strategy_since(strategy_id, since)
