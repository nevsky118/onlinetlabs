"""Unit tests for HistoryPgListener (PostgreSQL LISTEN history_events)."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_sdk.testing import autotest

from src.history_listener_pg import HistoryPgListener


@pytest.fixture
def broker():
    """EventBroker mock, only publish() is of interest here."""
    b = MagicMock()
    b.publish = AsyncMock()
    return b


@pytest.fixture
def listener(broker):
    return HistoryPgListener("postgres://stub", broker)


class TestOnNotify:
    """`_on_notify` is a synchronous asyncpg callback, it turns a payload into a publish task."""

    @autotest.num("3341")
    @autotest.external_id("fd6c3cf9-1c33-4dd0-b2ea-df89d724ca4c")
    @autotest.name(
        "HistoryPgListener._on_notify: publishes a history.event envelope for a valid payload"
    )
    async def test_fd6c3cf9_publishes_history_event_envelope_on_valid_payload(
        self, listener, broker
    ):
        with autotest.step("Arrange: a valid history event payload"):
            payload = json.dumps(
                {
                    "session_id": "sess-1",
                    "event_type": "node.created",
                    "component_id": "n1",
                    "data": {"foo": "bar"},
                }
            )

        with autotest.step("Act: notify with the payload and let the publish task finish"):
            listener._on_notify(conn=None, pid=1, channel="history_events", payload=payload)

            # The callback schedules create_task → wait for it to finish.
            pending = list(listener._pending_publishes)
            assert pending, "_on_notify must schedule a publish task"
            await asyncio.gather(*pending)

        with autotest.step("Assert: the broker publishes a history.event envelope"):
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

    @autotest.num("3342")
    @autotest.external_id("31dd437f-1b24-4a32-b764-414ca235d1a0")
    @autotest.name("HistoryPgListener._on_notify: ignores a non-JSON payload")
    async def test_31dd437f_ignores_non_json_payload(self, listener, broker):
        with autotest.step("Act: notify with a non-JSON payload"):
            listener._on_notify(conn=None, pid=1, channel="history_events", payload="not-json{")

        with autotest.step("Assert: nothing is scheduled or published"):
            assert not listener._pending_publishes
            broker.publish.assert_not_awaited()

    @autotest.num("3343")
    @autotest.external_id("2e84aefb-7eaa-400b-a7bf-38616af561c8")
    @autotest.name("HistoryPgListener._on_notify: ignores a payload missing session_id")
    async def test_2e84aefb_ignores_payload_without_session_id(self, listener, broker):
        with autotest.step("Arrange: a payload missing session_id"):
            payload = json.dumps({"event_type": "node.created", "data": {}})

        with autotest.step("Act: notify with the payload"):
            listener._on_notify(conn=None, pid=1, channel="history_events", payload=payload)

        with autotest.step("Assert: nothing is scheduled or published"):
            assert not listener._pending_publishes
            broker.publish.assert_not_awaited()


class TestStartStop:
    """Lifecycle of the background task."""

    @autotest.num("3344")
    @autotest.external_id("b550dc44-e332-4ed2-a626-b1796749b122")
    @autotest.name("HistoryPgListener.stop: cancels the running task and clears state")
    async def test_b550dc44_stop_cancels_running_task_and_clears_state(self, listener, monkeypatch):
        with autotest.step("Arrange: stub asyncpg.connect with a fake connection"):
            # Mock asyncpg.connect so that _run does not try to connect for real.
            fake_conn = AsyncMock()
            fake_conn.add_listener = AsyncMock()
            fake_conn.execute = AsyncMock()
            fake_conn.fetchval = AsyncMock(return_value=1)
            fake_conn.close = AsyncMock()

            async def fake_connect(dsn):
                return fake_conn

            monkeypatch.setattr("src.history_listener_pg.asyncpg.connect", fake_connect)

        with autotest.step("Act: start the listener and wait for it to attach LISTEN"):
            await listener.start()
            # Let _run run connect + add_listener + LISTEN.
            for _ in range(20):
                await asyncio.sleep(0)
                if fake_conn.add_listener.await_count:
                    break

        with autotest.step("Assert: it listened on history_events with the notify callback"):
            fake_conn.add_listener.assert_awaited_with("history_events", listener._on_notify)

        with autotest.step("Act: stop the listener"):
            await listener.stop()

        with autotest.step("Assert: the task and connection are cleared"):
            assert listener._task is None
            assert listener._conn is None
