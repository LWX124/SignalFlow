"""Strategy registry."""

from typing import Dict, Type
from src.strategies.base import BaseStrategy


class StrategyRegistry:
    """Strategy registration center."""

    _strategies: Dict[str, BaseStrategy] = {}

    @classmethod
    def register(cls, strategy: BaseStrategy) -> None:
        cls._strategies[strategy.strategy_id] = strategy

    @classmethod
    def get(cls, strategy_id: str) -> BaseStrategy | None:
        return cls._strategies.get(strategy_id)

    @classmethod
    def list_all(cls) -> list[BaseStrategy]:
        return list(cls._strategies.values())

    @classmethod
    def list_ids(cls) -> list[str]:
        return list(cls._strategies.keys())

    @classmethod
    def unregister(cls, strategy_id: str) -> bool:
        if strategy_id in cls._strategies:
            del cls._strategies[strategy_id]
            return True
        return False

    @classmethod
    def clear(cls) -> None:
        cls._strategies.clear()
