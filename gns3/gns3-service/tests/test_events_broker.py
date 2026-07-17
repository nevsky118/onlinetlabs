"""Unit-тесты EventBroker (Redis Streams)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.events_broker import EventBroker


@pytest.fixture
def broker():
    """EventBroker с замоканным aioredis-клиентом."""
    fake_redis = AsyncMock()
    with patch("src.events_broker.aioredis.from_url", return_value=fake_redis):
        b = EventBroker("redis://localhost:6379/0")
    # Заменяем напрямую, чтобы исключить любые случайные реальные вызовы.
    b._redis = fake_redis
    return b, fake_redis


class TestPublish:
    async def test_publish_calls_xadd_with_stream_key_and_serialized_payload(self, broker):
        b, redis = broker
        event = {"type": "node.updated", "node_id": "n1"}

        await b.publish("sess-1", event)

        redis.xadd.assert_awaited_once()
        args, kwargs = redis.xadd.await_args
        # Первый позиционный — ключ стрима.
        assert args[0] == "sessions:sess-1:events"
        # Второй позиционный — словарь полей.
        fields = args[1]
        assert json.loads(fields["payload"]) == event
        # Trim approximation параметры.
        assert kwargs.get("maxlen") == 1000
        assert kwargs.get("approximate") is True

    async def test_publish_swallows_non_serializable_event(self, broker):
        b, redis = broker
        # set() не сериализуется в JSON.
        await b.publish("sess-1", {"bad": {1, 2, 3}})
        redis.xadd.assert_not_awaited()


class TestSubscribe:
    async def test_subscribe_yields_parsed_event_from_xread(self, broker):
        b, redis = broker
        event = {"type": "node.updated", "node_id": "n1"}
        # Один батч с одной записью, затем StopAsyncIteration через CancelledError.
        redis.xread = AsyncMock(
            side_effect=[
                [("sessions:sess-1:events", [("1-0", {"payload": json.dumps(event)})])],
            ]
            + [Exception("stop loop")] * 5
        )

        agen = b.subscribe("sess-1")
        first = await agen.__anext__()
        assert first == event
        # Проверяем, что xread звался с правильным stream_key и стартом "$".
        args, kwargs = redis.xread.await_args_list[0]
        streams = args[0]
        assert "sessions:sess-1:events" in streams
        assert streams["sessions:sess-1:events"] == "$"
        assert kwargs.get("block") == 5000
        await agen.aclose()
