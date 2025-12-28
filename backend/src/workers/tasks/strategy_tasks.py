"""Strategy execution tasks."""

import asyncio
from datetime import datetime, timedelta

from src.workers.celery_app import celery_app
from src.strategies.base import StrategyContext
from src.strategies.registry import StrategyRegistry
from src.strategies.arbitrage.qdii_premium import QDIIPremiumStrategy
from src.providers.jisilu.qdii_provider import JisiluQDIIProvider
from src.providers.base import DataCapability
from src.core.logging import get_logger

logger = get_logger(__name__)


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Register strategies
StrategyRegistry.register(QDIIPremiumStrategy())


@celery_app.task(bind=True, max_retries=3)
def run_strategy(self, strategy_id: str, params: dict | None = None):
    """Run a specific strategy."""
    logger.info("Running strategy", strategy_id=strategy_id)

    strategy = StrategyRegistry.get(strategy_id)
    if not strategy:
        logger.error("Strategy not found", strategy_id=strategy_id)
        return {"status": "error", "message": "Strategy not found"}

    async def _run():
        # Fetch required data
        data = {}

        if "qdii_snapshot" in strategy.required_data:
            provider = JisiluQDIIProvider()
            try:
                data["qdii_snapshot"] = await provider.fetch(DataCapability.QDII_SNAPSHOT)
            finally:
                await provider.close()

        # Create context
        merged_params = strategy.merge_params(params or {})
        context = StrategyContext(
            strategy_id=strategy_id,
            params=merged_params,
            data=data,
            timestamp=datetime.utcnow(),
        )

        # Compute signals
        signals = await strategy.compute(context)

        logger.info(
            "Strategy execution complete",
            strategy_id=strategy_id,
            signal_count=len(signals),
        )

        return {
            "status": "success",
            "strategy_id": strategy_id,
            "signal_count": len(signals),
            "signals": [s.to_dict() for s in signals],
            "timestamp": datetime.utcnow().isoformat(),
        }

    try:
        return run_async(_run())
    except Exception as exc:
        logger.error("Strategy execution failed", strategy_id=strategy_id, error=str(exc))
        self.retry(exc=exc, countdown=60)


@celery_app.task
def run_all_strategies():
    """Run all registered strategies."""
    logger.info("Running all strategies")

    results = []
    for strategy_id in StrategyRegistry.list_ids():
        result = run_strategy.delay(strategy_id)
        results.append({"strategy_id": strategy_id, "task_id": result.id})

    return {
        "status": "started",
        "strategies": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@celery_app.task
def compute_strategy_metrics(strategy_id: str, days: int = 30):
    """Compute performance metrics for a strategy."""
    logger.info("Computing strategy metrics", strategy_id=strategy_id, days=days)
    # TODO: Implement metrics computation
    return {"status": "not_implemented", "strategy_id": strategy_id}
