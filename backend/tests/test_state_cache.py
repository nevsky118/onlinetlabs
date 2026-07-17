import json
from unittest.mock import AsyncMock

import pytest

from sessions.state_cache import StateCache


@pytest.mark.asyncio
async def test_get_returns_none_on_miss():
    redis = AsyncMock()
    redis.get.return_value = None
    cache = StateCache(redis, ttl_seconds=5)
    assert (await cache.get("11111111-1111-1111-1111-111111111111")) is None


@pytest.mark.asyncio
async def test_get_returns_parsed_state_on_hit():
    redis = AsyncMock()
    state = {"sessionId": "11111111-1111-1111-1111-111111111111", "nodes": []}
    redis.get.return_value = json.dumps(state)
    cache = StateCache(redis, ttl_seconds=5)
    assert await cache.get("11111111-1111-1111-1111-111111111111") == state


@pytest.mark.asyncio
async def test_set_writes_json_with_ttl():
    redis = AsyncMock()
    cache = StateCache(redis, ttl_seconds=5)
    state = {"sessionId": "11111111-1111-1111-1111-111111111111", "nodes": []}
    await cache.set("11111111-1111-1111-1111-111111111111", state)
    redis.set.assert_awaited_once_with(
        "session:state:11111111-1111-1111-1111-111111111111",
        json.dumps(state),
        ex=5,
    )


@pytest.mark.asyncio
async def test_invalidate_deletes_key():
    redis = AsyncMock()
    cache = StateCache(redis, ttl_seconds=5)
    await cache.invalidate("11111111-1111-1111-1111-111111111111")
    redis.delete.assert_awaited_once_with("session:state:11111111-1111-1111-1111-111111111111")


@pytest.mark.asyncio
async def test_get_returns_none_on_corrupted_json():
    redis = AsyncMock()
    redis.get.return_value = "not valid json {{{"
    cache = StateCache(redis, ttl_seconds=5)
    assert (await cache.get("any-id")) is None
