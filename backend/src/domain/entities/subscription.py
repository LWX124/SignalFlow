"""Subscription entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.constants import SubscriptionStatus, DeliveryChannel


@dataclass
class SubscriptionEntity:
    """Subscription domain entity."""

    id: UUID
    user_id: UUID
    strategy_id: str
    params: dict[str, Any] = field(default_factory=dict)
    channels: list[str] = field(default_factory=lambda: [DeliveryChannel.SITE.value])
    cooldown_seconds: int = 3600
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    last_signal_at: datetime | None = None
    signal_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == SubscriptionStatus.ACTIVE

    def can_receive_signal(self, now: datetime | None = None) -> bool:
        """
        Check if subscription can receive a new signal based on cooldown.
        """
        if not self.is_active:
            return False

        if self.last_signal_at is None:
            return True

        if now is None:
            now = datetime.utcnow()

        elapsed = (now - self.last_signal_at).total_seconds()
        return elapsed >= self.cooldown_seconds

    def pause(self) -> None:
        """Pause the subscription."""
        self.status = SubscriptionStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume(self) -> None:
        """Resume the subscription."""
        self.status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel the subscription."""
        self.status = SubscriptionStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def record_signal(self, signal_time: datetime | None = None) -> None:
        """Record that a signal was sent."""
        self.last_signal_at = signal_time or datetime.utcnow()
        self.signal_count += 1
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "strategy_id": self.strategy_id,
            "params": self.params,
            "channels": self.channels,
            "cooldown_seconds": self.cooldown_seconds,
            "status": self.status.value,
            "last_signal_at": self.last_signal_at.isoformat() if self.last_signal_at else None,
            "signal_count": self.signal_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
