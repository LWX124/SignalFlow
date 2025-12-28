"""Redis client for caching."""

import json
from typing import Any

import redis.asyncio as redis

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client wrapper."""

    def __init__(self, url: str | None = None):
        self._url = url or settings.redis_url
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._client = redis.from_url(self._url, decode_responses=True)
        logger.info("Connected to Redis")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            logger.info("Disconnected from Redis")

    @property
    def client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return self._client

    async def get(self, key: str) -> str | None:
        """Get a value by key."""
        return await self.client.get(key)

    async def get_json(self, key: str) -> Any | None:
        """Get and deserialize JSON value."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: str,
        expire: int | None = None,
    ) -> None:
        """Set a value with optional expiration (seconds)."""
        await self.client.set(key, value, ex=expire)

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> None:
        """Serialize and set JSON value."""
        await self.set(key, json.dumps(value, default=str), expire)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        await self.client.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await self.client.delete(*keys)
        return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return await self.client.exists(key) > 0

    async def incr(self, key: str) -> int:
        """Increment a value."""
        return await self.client.incr(key)

    async def expire(self, key: str, seconds: int) -> None:
        """Set expiration on a key."""
        await self.client.expire(key, seconds)

    async def publish(self, channel: str, message: str) -> None:
        """Publish a message to a channel."""
        await self.client.publish(channel, message)

    async def lpush(self, key: str, *values: str) -> int:
        """Push values to the head of a list."""
        return await self.client.lpush(key, *values)

    async def rpop(self, key: str) -> str | None:
        """Pop from the tail of a list."""
        return await self.client.rpop(key)

    async def lrange(self, key: str, start: int, stop: int) -> list[str]:
        """Get a range of elements from a list."""
        return await self.client.lrange(key, start, stop)


# Global Redis client instance
_redis_client: RedisClient | None = None


async def get_redis() -> RedisClient:
    """Get the global Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    return _redis_client


async def close_redis() -> None:
    """Close the global Redis client."""
    global _redis_client
    if _redis_client:
        await _redis_client.disconnect()
        _redis_client = None
