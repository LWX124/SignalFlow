"""Initialize database with seed data."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infra.database.connection import AsyncSessionLocal
from src.infra.database.models import Strategy
from src.core.constants import StrategyType, RiskLevel, UserTier


async def seed_strategies():
    """Seed initial strategies."""
    strategies = [
        Strategy(
            id="qdii_premium_arb",
            version="1.0.0",
            name="QDII溢价套利",
            description="监控QDII基金溢价率，当溢价率超过阈值时提示套利机会。高溢价时存在申购套利空间，低溢价/折价时关注买入机会。",
            type=StrategyType.ARBITRAGE,
            markets=["SH", "SZ"],
            risk_level=RiskLevel.MEDIUM,
            frequency_hint="intraday",
            params_schema={
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
            },
            default_params={
                "premium_threshold_high": 5.0,
                "premium_threshold_low": -3.0,
                "min_volume": 5000000,
            },
            default_cooldown=7200,
            is_active=True,
            is_public=True,
            tier_required=UserTier.FREE,
        ),
    ]

    async with AsyncSessionLocal() as session:
        for strategy in strategies:
            existing = await session.get(Strategy, strategy.id)
            if not existing:
                session.add(strategy)
                print(f"Added strategy: {strategy.name}")
            else:
                print(f"Strategy already exists: {strategy.name}")

        await session.commit()


async def main():
    print("Initializing database with seed data...")
    await seed_strategies()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
