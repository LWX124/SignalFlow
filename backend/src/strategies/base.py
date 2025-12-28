"""Base strategy class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.core.constants import SignalSide, Market


@dataclass
class Signal:
    """Strategy output signal."""

    strategy_id: str
    strategy_version: str
    symbol: str
    market: Market
    side: SignalSide
    confidence: float
    reason_points: list[str]
    snapshot: dict[str, Any]
    risk_tags: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str | None = None
    ai_explain: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "symbol": self.symbol,
            "market": self.market.value if isinstance(self.market, Market) else self.market,
            "side": self.side.value if isinstance(self.side, SignalSide) else self.side,
            "confidence": self.confidence,
            "reason_points": self.reason_points,
            "risk_tags": self.risk_tags,
            "snapshot": self.snapshot,
            "timestamp": self.timestamp.isoformat(),
            "ai_explain": self.ai_explain,
        }


@dataclass
class StrategyContext:
    """Strategy execution context."""

    strategy_id: str
    params: dict[str, Any]
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def get_data(self, key: str) -> Any:
        return self.data.get(key)

    def get_param(self, key: str, default: Any = None) -> Any:
        return self.params.get(key, default)


class BaseStrategy(ABC):
    """Base class for all strategies."""

    strategy_id: str = ""
    version: str = "1.0.0"
    name: str = ""
    description: str = ""
    required_data: list[str] = []
    params_schema: dict[str, Any] = {}
    default_cooldown: int = 3600

    @abstractmethod
    async def compute(self, context: StrategyContext) -> list[Signal]:
        pass

    def risk_check(self, signal: Signal, context: StrategyContext) -> tuple[bool, list[str]]:
        risk_tags = []
        snapshot = signal.snapshot

        volume = snapshot.get("volume", 0)
        if volume and volume < 1000000:
            risk_tags.append("低流动性")

        change_pct = snapshot.get("change_pct", 0)
        if change_pct > 9.5:
            risk_tags.append("涨停")
        elif change_pct < -9.5:
            risk_tags.append("跌停")

        return len(risk_tags) == 0, risk_tags

    def dedup_key(self, signal: Signal) -> str:
        return f"{self.strategy_id}:{signal.symbol}:{signal.side.value}"

    def validate_params(self, params: dict[str, Any]) -> tuple[bool, list[str]]:
        errors = []
        schema = self.params_schema
        required = schema.get("required", [])
        for param in required:
            if param not in params:
                errors.append(f"缺少必需参数: {param}")

        properties = schema.get("properties", {})
        for param_name, param_value in params.items():
            if param_name not in properties:
                continue
            prop_schema = properties[param_name]
            prop_type = prop_schema.get("type")

            if prop_type == "number" and not isinstance(param_value, (int, float)):
                errors.append(f"参数 '{param_name}' 必须是数字")
            elif prop_type == "number":
                min_val = prop_schema.get("minimum")
                max_val = prop_schema.get("maximum")
                if min_val is not None and param_value < min_val:
                    errors.append(f"参数 '{param_name}' 必须 >= {min_val}")
                if max_val is not None and param_value > max_val:
                    errors.append(f"参数 '{param_name}' 必须 <= {max_val}")

        return len(errors) == 0, errors

    def get_default_params(self) -> dict[str, Any]:
        defaults = {}
        properties = self.params_schema.get("properties", {})
        for param_name, prop_schema in properties.items():
            if "default" in prop_schema:
                defaults[param_name] = prop_schema["default"]
        return defaults

    def merge_params(self, user_params: dict[str, Any]) -> dict[str, Any]:
        result = self.get_default_params()
        result.update(user_params)
        return result
