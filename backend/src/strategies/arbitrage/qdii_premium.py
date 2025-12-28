"""QDII Premium Arbitrage Strategy."""

from src.strategies.base import BaseStrategy, Signal, StrategyContext
from src.core.constants import SignalSide, Market


class QDIIPremiumStrategy(BaseStrategy):
    """
    QDII溢价套利策略

    当QDII基金溢价率超过阈值时，提示套利机会：
    - 高溢价（>5%）：卖出/申购套利机会
    - 低溢价/折价（<-3%）：买入/赎回套利机会
    """

    strategy_id = "qdii_premium_arb"
    version = "1.0.0"
    name = "QDII溢价套利"
    description = "监控QDII基金溢价率，提示套利机会"

    required_data = ["qdii_snapshot"]

    params_schema = {
        "type": "object",
        "properties": {
            "premium_threshold_high": {
                "type": "number",
                "default": 5.0,
                "minimum": 1.0,
                "maximum": 20.0,
                "description": "高溢价阈值 (%)",
            },
            "premium_threshold_low": {
                "type": "number",
                "default": -3.0,
                "minimum": -20.0,
                "maximum": -1.0,
                "description": "低溢价/折价阈值 (%)",
            },
            "min_volume": {
                "type": "number",
                "default": 5000000,
                "description": "最小成交额 (元)",
            },
        },
        "required": ["premium_threshold_high", "premium_threshold_low"],
    }

    default_cooldown = 7200  # 2小时

    async def compute(self, context: StrategyContext) -> list[Signal]:
        signals = []
        params = context.params

        threshold_high = params.get("premium_threshold_high", 5.0)
        threshold_low = params.get("premium_threshold_low", -3.0)
        min_volume = params.get("min_volume", 5000000)

        qdii_data = context.data.get("qdii_snapshot", [])

        for item in qdii_data:
            premium_rate = item.get("premium_rate", 0)
            volume = item.get("volume", 0)

            if volume < min_volume:
                continue

            reason_points = []
            risk_tags = []
            side = None
            confidence = 0.0

            if premium_rate >= threshold_high:
                side = SignalSide.OPPORTUNITY
                confidence = min(0.9, 0.5 + (premium_rate - threshold_high) * 0.05)
                reason_points = [
                    f"溢价率 {premium_rate:.2f}%，超过阈值 {threshold_high}%",
                    f"当前价格 {item.get('price')}，估算净值 {item.get('nav_estimate')}",
                    "存在申购套利空间",
                ]
                if item.get("apply_status") == "限制":
                    risk_tags.append("申购受限")
                    confidence *= 0.7

            elif premium_rate <= threshold_low:
                side = SignalSide.OBSERVE
                confidence = min(0.9, 0.5 + abs(premium_rate - threshold_low) * 0.05)
                reason_points = [
                    f"折价率 {premium_rate:.2f}%，超过阈值 {threshold_low}%",
                    f"当前价格 {item.get('price')}，估算净值 {item.get('nav_estimate')}",
                    "关注买入机会",
                ]

            if side:
                code = item.get("code", "")
                market = Market.SH if code.startswith("5") else Market.SZ

                signal = Signal(
                    strategy_id=self.strategy_id,
                    strategy_version=self.version,
                    symbol=code,
                    market=market,
                    side=side,
                    confidence=confidence,
                    reason_points=reason_points,
                    risk_tags=risk_tags,
                    snapshot={
                        "price": item.get("price"),
                        "nav_estimate": item.get("nav_estimate"),
                        "premium_rate": premium_rate,
                        "volume": volume,
                        "change_pct": item.get("change_pct"),
                        "apply_status": item.get("apply_status"),
                        "name": item.get("name"),
                    },
                )

                passed, additional_tags = self.risk_check(signal, context)
                signal.risk_tags.extend(additional_tags)

                signals.append(signal)

        return signals
