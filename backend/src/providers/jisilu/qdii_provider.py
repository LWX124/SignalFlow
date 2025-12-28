"""Jisilu QDII data provider."""

import httpx
from datetime import datetime
from typing import Any

from src.providers.base import BaseProvider, DataCapability, ProviderHealth
from src.core.logging import get_logger

logger = get_logger(__name__)


class JisiluQDIIProvider(BaseProvider):
    """
    集思录QDII数据源

    数据来源: https://www.jisilu.cn/data/qdii/
    """

    provider_id = "jisilu_qdii"
    name = "集思录QDII"
    capabilities = [DataCapability.QDII_SNAPSHOT]
    rate_limit_per_minute = 10

    BASE_URL = "https://www.jisilu.cn/data/qdii/qdii_list/"

    def __init__(self):
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://www.jisilu.cn/data/qdii/",
            },
            timeout=30.0,
        )

    async def fetch(self, capability: DataCapability, **kwargs) -> list[dict[str, Any]]:
        if capability != DataCapability.QDII_SNAPSHOT:
            raise ValueError(f"Unsupported capability: {capability}")

        try:
            response = await self._client.get(self.BASE_URL)
            response.raise_for_status()

            data = response.json()
            rows = data.get("rows", [])

            return [self.normalize(row) for row in rows]

        except Exception as e:
            logger.error("Failed to fetch QDII data", error=str(e))
            raise

    def normalize(self, raw_data: dict) -> dict[str, Any]:
        cell = raw_data.get("cell", {})

        return {
            "code": cell.get("fund_id", ""),
            "name": cell.get("fund_nm", ""),
            "price": self._parse_float(cell.get("price", 0)),
            "change_pct": self._parse_float(cell.get("increase_rt", "0%")),
            "volume": self._parse_float(cell.get("amount", 0)),
            "nav_t1": self._parse_float(cell.get("nav", 0)),
            "nav_estimate": self._parse_float(cell.get("estimate_value", 0)),
            "premium_rate": self._parse_float(cell.get("discount_rt", "0%")),
            "apply_status": cell.get("apply_status", ""),
            "redeem_status": cell.get("redeem_status", ""),
            "index_nm": cell.get("index_nm", ""),
            "crawl_time": datetime.utcnow().isoformat(),
        }

    def _parse_float(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.strip().replace("%", "").replace(",", "")
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    async def health_check(self) -> ProviderHealth:
        try:
            start = datetime.utcnow()
            response = await self._client.head(self.BASE_URL)
            latency = (datetime.utcnow() - start).total_seconds() * 1000

            return ProviderHealth(
                is_healthy=response.status_code == 200,
                last_success=datetime.utcnow(),
                last_error=None,
                latency_ms=latency,
            )
        except Exception as e:
            return ProviderHealth(
                is_healthy=False,
                last_success=None,
                last_error=str(e),
                latency_ms=-1,
            )

    async def close(self):
        await self._client.aclose()
