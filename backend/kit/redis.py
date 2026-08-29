"""One place a Redis client is built."""

import redis.asyncio as aioredis

from config import settings


def redis_client(*, decode_responses: bool = True) -> aioredis.Redis:
    """A client on the configured Redis URL."""
    return aioredis.from_url(settings.redis.url, decode_responses=decode_responses)
