"""Unit-тесты HistoryPgListener (PostgreSQL LISTEN history_events)."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.history_listener_pg import HistoryPgListener


@pytest.fixture
def broker():
    """EventBroker mock — нас интересует только publish()."""
    b = MagicMock()
    b.publish = AsyncMock()
    return b


@pytest.fixture
def listener(broker):
    return HistoryPgListener("postgres://stub", broker)


class TestOnNotify:
    """`_on_notify` — синхронный колбэк asyncpg, превращает payload в publish-таск."""

    async def test_publishes_history_event_envelope_on_valid_payload(self, listener, broker):
        payload = json.dumps(
            {
                "session_id": "sess-1",
                "event_type": "node.created",
                "component_id": "n1",
                "data": {"foo": "bar"},
            }
        )
        listener._on_notify(conn=None, pid=1, channel="history_events", payload=payload)

        # Колбэк планирует create_task → ждём его завершения.
        pending = list(listener._pending_publishes)
        assert pending, "_on_notify must schedule a publish task"
        await asyncio.gather(*pending)

        broker.publish.assert_awaited_once()
        args, _ = broker.publish.await_args
        session_id, event = args
        assert session_id == "sess-1"
        assert event["type"] == "history.event"
        assert event["payload"] == {
            "event_type": "node.created",
            "component_id": "n1",
            "data": {"foo": "bar"},
        }
        assert "timestamp" in event

    async def test_ignores_non_json_payload(self, listener, broker):
        listener._on_notify(conn=None, pid=1, channel="history_events", payload="not-json{")
        assert not listener._pending_publishes
        broker.publish.assert_not_awaited()

    async def test_ignores_payload_without_session_id(self, listener, broker):
        payload = json.dumps({"event_type": "node.created", "data": {}})
        listener._on_notify(conn=None, pid=1, channel="history_events", payload=payload)
        assert not listener._pending_publishes
        broker.publish.assert_not_awaited()


class TestStartStop:
    """Жизненный цикл фоновой таски."""

    async def test_stop_cancels_running_task_and_clears_state(self, listener, monkeypatch):
        # Замокаем asyncpg.connect, чтобы _run не пытался реально приконнектиться.
        fake_conn = AsyncMock()
        fake_conn.add_listener = AsyncMock()
        fake_conn.execute = AsyncMock()
        fake_conn.fetchval = AsyncMock(return_value=1)
        fake_conn.close = AsyncMock()

        async def fake_connect(dsn):
            return fake_conn

        monkeypatch.setattr("src.history_listener_pg.asyncpg.connect", fake_connect)

        await listener.start()
        # Дать _run выполнить connect + add_listener + LISTEN.
        for _ in range(20):
            await asyncio.sleep(0)
            if fake_conn.add_listener.await_count:
                break

        fake_conn.add_listener.assert_awaited_with("history_events", listener._on_notify)

        await listener.stop()
        assert listener._task is None
        assert listener._conn is None
