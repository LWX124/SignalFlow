"""Base data provider class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class DataCapability(str, Enum):
    """Data source capability types."""

    QDII_SNAPSHOT = "qdii_snapshot"
    ETF_SNAPSHOT = "etf_snapshot"
    STOCK_QUOTE = "stock_quote"
    PRICE_BARS = "price_bars"
    NEWS = "news"
    ANNOUNCEMENT = "announcement"


@dataclass
class ProviderHealth:
    """Provider health status."""

    is_healthy: bool
    last_success: datetime | None
    last_error: str | None
    latency_ms: float


class BaseProvider(ABC):
    """Base class for data providers."""

    provider_id: str = ""
    name: str = ""
    capabilities: list[DataCapability] = []
    rate_limit_per_minute: int = 60

    @abstractmethod
    async def fetch(self, capability: DataCapability, **kwargs) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        pass

    def normalize(self, raw_data: Any) -> dict[str, Any]:
        return raw_data
