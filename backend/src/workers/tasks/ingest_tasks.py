"""Data ingestion tasks."""

import asyncio
from datetime import datetime

from src.workers.celery_app import celery_app
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


@celery_app.task(bind=True, max_retries=3)
def fetch_qdii_data(self):
    """Fetch QDII data from Jisilu."""
    logger.info("Starting QDII data fetch")

    async def _fetch():
        provider = JisiluQDIIProvider()
        try:
            data = await provider.fetch(DataCapability.QDII_SNAPSHOT)
            logger.info("Fetched QDII data", count=len(data))

            # Here you would store data to database
            # For now, just return the count
            return {
                "status": "success",
                "count": len(data),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("Failed to fetch QDII data", error=str(e))
            raise
        finally:
            await provider.close()

    try:
        return run_async(_fetch())
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task
def fetch_stock_quotes(symbols: list[str]):
    """Fetch stock quotes for given symbols."""
    logger.info("Fetching stock quotes", symbols=symbols)
    # TODO: Implement stock quote fetching
    return {"status": "not_implemented", "symbols": symbols}


@celery_app.task
def fetch_news():
    """Fetch latest news."""
    logger.info("Fetching news")
    # TODO: Implement news fetching
    return {"status": "not_implemented"}
