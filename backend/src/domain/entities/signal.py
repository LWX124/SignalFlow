"""Signal entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.constants import SignalSide, Market


@dataclass
class SignalEntity:
    """Signal domain entity."""

    strategy_id: str
    strategy_version: str
    symbol: str
    market: Market
    side: SignalSide
    confidence: float
    reason_points: list[str]
    snapshot: dict[str, Any]
    id: UUID | None = None
    risk_tags: list[str] = field(default_factory=list)
    dedup_key: str | None = None
    ai_explain: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Generate dedup_key if not provided."""
        if self.dedup_key is None:
            self.dedup_key = f"{self.strategy_id}:{self.symbol}:{self.side.value}"

    @property
    def has_risks(self) -> bool:
        """Check if signal has any risk tags."""
        return len(self.risk_tags) > 0

    @property
    def is_high_confidence(self) -> bool:
        """Check if signal has high confidence (>= 0.7)."""
        return self.confidence >= 0.7

    def add_risk_tag(self, tag: str) -> None:
        """Add a risk tag."""
        if tag not in self.risk_tags:
            self.risk_tags.append(tag)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "symbol": self.symbol,
            "market": self.market.value,
            "side": self.side.value,
            "confidence": self.confidence,
            "reason_points": self.reason_points,
            "risk_tags": self.risk_tags,
            "snapshot": self.snapshot,
            "dedup_key": self.dedup_key,
            "ai_explain": self.ai_explain,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SignalEntity":
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]) if data.get("id") else None,
            strategy_id=data["strategy_id"],
            strategy_version=data["strategy_version"],
            symbol=data["symbol"],
            market=Market(data["market"]),
            side=SignalSide(data["side"]),
            confidence=data["confidence"],
            reason_points=data["reason_points"],
            risk_tags=data.get("risk_tags", []),
            snapshot=data["snapshot"],
            dedup_key=data.get("dedup_key"),
            ai_explain=data.get("ai_explain"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )
