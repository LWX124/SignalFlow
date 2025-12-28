"""Market-related domain events."""

from dataclasses import dataclass, field
from typing import Any

from src.domain.events.base import DomainEvent


@dataclass
class DataUpdatedEvent(DomainEvent):
    """Event fired when market data is updated."""

    event_type: str = "DataUpdated"
    provider_id: str = ""
    capability: str = ""  # e.g., "qdii_snapshot", "stock_quote"
    symbols: list[str] = field(default_factory=list)
    record_count: int = 0

    def _payload(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "capability": self.capability,
            "symbols": self.symbols,
            "record_count": self.record_count,
        }


@dataclass
class ProviderHealthChangedEvent(DomainEvent):
    """Event fired when a provider's health status changes."""

    event_type: str = "ProviderHealthChanged"
    provider_id: str = ""
    is_healthy: bool = True
    error_message: str | None = None

    def _payload(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "is_healthy": self.is_healthy,
            "error_message": self.error_message,
        }
