"""Signal-related domain events."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.domain.events.base import DomainEvent
from src.core.constants import SignalSide, SubscriptionStatus


@dataclass
class SignalCreatedEvent(DomainEvent):
    """Event fired when a new signal is created."""

    event_type: str = "SignalCreated"
    signal_id: UUID | None = None
    strategy_id: str = ""
    symbol: str = ""
    market: str = ""
    side: SignalSide = SignalSide.OBSERVE
    confidence: float = 0.0

    def _payload(self) -> dict[str, Any]:
        return {
            "signal_id": str(self.signal_id) if self.signal_id else None,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "market": self.market,
            "side": self.side.value,
            "confidence": self.confidence,
        }


@dataclass
class SubscriptionCreatedEvent(DomainEvent):
    """Event fired when a new subscription is created."""

    event_type: str = "SubscriptionCreated"
    subscription_id: UUID | None = None
    user_id: UUID | None = None
    strategy_id: str = ""

    def _payload(self) -> dict[str, Any]:
        return {
            "subscription_id": str(self.subscription_id) if self.subscription_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "strategy_id": self.strategy_id,
        }


@dataclass
class SubscriptionUpdatedEvent(DomainEvent):
    """Event fired when a subscription is updated."""

    event_type: str = "SubscriptionUpdated"
    subscription_id: UUID | None = None
    user_id: UUID | None = None
    strategy_id: str = ""
    old_status: SubscriptionStatus | None = None
    new_status: SubscriptionStatus | None = None

    def _payload(self) -> dict[str, Any]:
        return {
            "subscription_id": str(self.subscription_id) if self.subscription_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "strategy_id": self.strategy_id,
            "old_status": self.old_status.value if self.old_status else None,
            "new_status": self.new_status.value if self.new_status else None,
        }


@dataclass
class SignalDeliveredEvent(DomainEvent):
    """Event fired when a signal is delivered to a user."""

    event_type: str = "SignalDelivered"
    signal_id: UUID | None = None
    user_id: UUID | None = None
    subscription_id: UUID | None = None
    channel: str = ""
    success: bool = True
    error_message: str | None = None

    def _payload(self) -> dict[str, Any]:
        return {
            "signal_id": str(self.signal_id) if self.signal_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "subscription_id": str(self.subscription_id) if self.subscription_id else None,
            "channel": self.channel,
            "success": self.success,
            "error_message": self.error_message,
        }
