"""Unit tests for EventBroker (Redis Streams)."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in

from src.events_broker import EventBroker

pytestmark = [pytest.mark.unit]


@pytest.fixture
def broker():
    """EventBroker with a mocked aioredis client."""
    fake_redis = AsyncMock()
    with patch("src.events_broker.aioredis.from_url", return_value=fake_redis):
        event_broker = EventBroker("redis://localhost:6379/0")
    # Replace it directly to rule out any accidental real calls.
    event_broker._redis = fake_redis
    return event_broker, fake_redis


class TestPublish:
    @autotest.num("3297")
    @autotest.external_id("97b813d0-eafe-4357-b735-1e215f74f459")
    @autotest.name("EventBroker.publish: calls xadd with the stream key and serialized payload")
    async def test_97b813d0_publish_calls_xadd_with_stream_key_and_serialized_payload(self, broker):
        with autotest.step("Arrange: unpack the broker and build an event payload"):
            value, redis = broker
            event = {"type": "node.updated", "node_id": "n1"}

        with autotest.step("Act: publish the event"):
            await value.publish("sess-1", event)

        with autotest.step("Assert: xadd was called with the stream key, payload and trim opts"):
            redis.xadd.assert_awaited_once()
            args, kwargs = redis.xadd.await_args
            # First positional argument is the stream key.
            assert_equal(args[0], "sessions:sess-1:events", "args[0]")
            # Second positional argument is the field dict.
            fields = args[1]
            assert_equal(json.loads(fields["payload"]), event, "loads")
            # Trim approximation parameters.
            assert_equal(kwargs.get("maxlen"), 1000, "get")
            assert_equal(kwargs.get("approximate"), True, "get")

    @autotest.num("3298")
    @autotest.external_id("6cb73b6b-c8ea-4e62-bc73-0dd45a128ea8")
    @autotest.name("EventBroker.publish: swallows a non-serializable event without calling xadd")
    async def test_6cb73b6b_publish_swallows_non_serializable_event(self, broker):
        with autotest.step("Arrange: unpack the broker"):
            value, redis = broker

        with autotest.step("Act: publish an event with a non-JSON-serializable field"):
            # set() is not JSON-serializable.
            await value.publish("sess-1", {"bad": {1, 2, 3}})

        with autotest.step("Assert: the event is swallowed, xadd is never called"):
            redis.xadd.assert_not_awaited()


class TestSubscribe:
    @autotest.num("3299")
    @autotest.external_id("71a2acdd-9d9a-49ed-bea7-1cba29c219ae")
    @autotest.name("EventBroker.subscribe: yields the parsed event from xread")
    async def test_71a2acdd_subscribe_yields_parsed_event_from_xread(self, broker):
        with autotest.step("Arrange: unpack the broker and stub xread with one batch"):
            value, redis = broker
            event = {"type": "node.updated", "node_id": "n1"}
            # One batch with one entry, then StopAsyncIteration via CancelledError.
            redis.xread = AsyncMock(
                side_effect=[
                    [("sessions:sess-1:events", [("1-0", {"payload": json.dumps(event)})])],
                ]
                + [Exception("stop loop")] * 5
            )

        with autotest.step("Act: subscribe and pull the first event"):
            agen = value.subscribe("sess-1")
            first = await agen.__anext__()

        with autotest.step("Assert: the event is parsed and xread used the right stream/start"):
            assert_equal(first, event, "first")
            # Check that xread was called with the right stream_key and a "$" start.
            args, kwargs = redis.xread.await_args_list[0]
            streams = args[0]
            assert_in("sessions:sess-1:events", streams, "'sessions:sess-1:events'")
            assert_equal(streams["sessions:sess-1:events"], "$", "sessions:sess-1:events")
            assert_equal(kwargs.get("block"), 5000, "get")
            await agen.aclose()
