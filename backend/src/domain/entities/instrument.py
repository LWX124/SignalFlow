"""Instrument entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.constants import Market, InstrumentType


@dataclass
class InstrumentEntity:
    """Instrument/Security domain entity."""

    id: UUID
    symbol: str
    name: str
    market: Market
    type: InstrumentType
    exchange: str | None = None
    currency: str = "CNY"
    metadata: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def full_symbol(self) -> str:
        """Get full symbol with market prefix."""
        return f"{self.market.value}.{self.symbol}"

    @property
    def is_tradable(self) -> bool:
        """Check if instrument is tradable."""
        return self.is_active

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market.value,
            "type": self.type.value,
            "exchange": self.exchange,
            "currency": self.currency,
            "metadata": self.metadata,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
