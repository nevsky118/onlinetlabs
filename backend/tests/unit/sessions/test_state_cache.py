import json
from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none

from sessions.state_cache import StateCache

pytestmark = [pytest.mark.unit]


class TestStateCache:
    @pytest.mark.asyncio
    @autotest.num("3204")
    @autotest.external_id("91faa4b2-306c-4c8d-bfcc-1e1237cd5f20")
    @autotest.name("StateCache.get: returns None on a miss")
    async def test_91faa4b2_get_returns_none_on_miss(self):
        with autotest.step("Arrange: redis.get returns None (cache miss)"):
            redis = AsyncMock()
            redis.get.return_value = None
            cache = StateCache(redis, ttl_seconds=5)

        with autotest.step("Act+Assert: get returns None"):
            assert_is_none(
                await cache.get("11111111-1111-1111-1111-111111111111"),
                "cache miss",
            )

    @pytest.mark.asyncio
    @autotest.num("3205")
    @autotest.external_id("7e244144-16d1-4442-a1db-10da84e85c2e")
    @autotest.name("StateCache.get: returns parsed state on a hit")
    async def test_7e244144_get_returns_parsed_state_on_hit(self):
        with autotest.step("Arrange: redis.get returns a JSON-encoded state (cache hit)"):
            redis = AsyncMock()
            state = {"sessionId": "11111111-1111-1111-1111-111111111111", "nodes": []}
            redis.get.return_value = json.dumps(state)
            cache = StateCache(redis, ttl_seconds=5)

        with autotest.step("Act+Assert: get returns the parsed state"):
            assert_equal(
                await cache.get("11111111-1111-1111-1111-111111111111"),
                state,
                "cache miss",
            )

    @pytest.mark.asyncio
    @autotest.num("3206")
    @autotest.external_id("6795587c-19f3-478c-8bd4-f8c9856bb875")
    @autotest.name("StateCache.set: writes JSON with the configured TTL")
    async def test_6795587c_set_writes_json_with_ttl(self):
        with autotest.step("Arrange: cache and a state payload"):
            redis = AsyncMock()
            cache = StateCache(redis, ttl_seconds=5)
            state = {"sessionId": "11111111-1111-1111-1111-111111111111", "nodes": []}

        with autotest.step("Act: set"):
            await cache.set("11111111-1111-1111-1111-111111111111", state)

        with autotest.step("Assert: redis.set called with the JSON-encoded state and TTL"):
            redis.set.assert_awaited_once_with(
                "session:state:11111111-1111-1111-1111-111111111111",
                json.dumps(state),
                ex=5,
            )

    @pytest.mark.asyncio
    @autotest.num("3207")
    @autotest.external_id("8f82db15-9740-4ffa-9209-e21a1fb755bc")
    @autotest.name("StateCache.invalidate: deletes the cache key")
    async def test_8f82db15_invalidate_deletes_key(self):
        with autotest.step("Arrange: cache"):
            redis = AsyncMock()
            cache = StateCache(redis, ttl_seconds=5)

        with autotest.step("Act: invalidate"):
            await cache.invalidate("11111111-1111-1111-1111-111111111111")

        with autotest.step("Assert: redis.delete called with the cache key"):
            redis.delete.assert_awaited_once_with(
                "session:state:11111111-1111-1111-1111-111111111111"
            )

    @pytest.mark.asyncio
    @autotest.num("3208")
    @autotest.external_id("498b2733-e940-471b-a4f4-8a6a2a88430a")
    @autotest.name("StateCache.get: returns None on corrupted JSON")
    async def test_498b2733_get_returns_none_on_corrupted_json(self):
        with autotest.step("Arrange: redis.get returns invalid JSON"):
            redis = AsyncMock()
            redis.get.return_value = "not valid json {{{"
            cache = StateCache(redis, ttl_seconds=5)

        with autotest.step("Act+Assert: get returns None instead of raising"):
            assert_is_none(await cache.get("any-id"), "await cache.get('any-id')")
