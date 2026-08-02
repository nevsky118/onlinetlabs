"""Unit tests for the core Gns3WsProxy behavior."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.gns3_ws_proxy import Gns3WsProxy


@pytest.fixture
def broker():
    return AsyncMock()


@pytest.fixture
def admin_client():
    client = MagicMock()
    client.token = "admin-jwt-token"
    return client


@pytest.fixture
def proxy(broker, admin_client):
    """Proxy without Redis, which is correct for most unit tests."""
    return Gns3WsProxy(
        broker=broker,
        gns3_url="http://gns3:3080",
        admin_client=admin_client,
        redis_url=None,
    )


class TestConstants:
    """Sanity checks of the constants."""

    def test_lock_ttl_seconds(self):
        assert Gns3WsProxy._LOCK_TTL_SECONDS == 90

    def test_heartbeat_interval_seconds(self):
        assert Gns3WsProxy._HEARTBEAT_INTERVAL_SECONDS == 30

    def test_heartbeat_runs_well_inside_the_ttl(self):
        # A killed instance strands its projects for at most one TTL, and a live
        # one must renew with room to spare.
        assert Gns3WsProxy._HEARTBEAT_INTERVAL_SECONDS * 2 < Gns3WsProxy._LOCK_TTL_SECONDS


class TestBackoffDelay:
    """Exponential backoff, 1, 2, 4, 8, 16, 30, 30 for attempts 0-6."""

    @pytest.mark.parametrize(
        "attempt,expected",
        [
            (0, 1),
            (1, 2),
            (2, 4),
            (3, 8),
            (4, 16),
            (5, 30),
            (6, 30),
        ],
    )
    def test_backoff_delay_sequence(self, proxy, attempt, expected):
        assert proxy._backoff_delay(attempt) == expected


class TestLockKey:
    """Format of the Redis lock key."""

    def test_lock_key_format(self, proxy):
        assert proxy._lock_key("project-123") == "lock:ws_proxy:project-123"

    def test_lock_key_with_uuid(self, proxy):
        pid = "11111111-1111-1111-1111-111111111111"
        assert proxy._lock_key(pid) == f"lock:ws_proxy:{pid}"


class TestStartProjectIdempotency:
    """start_project is idempotent when a task already exists."""

    @pytest.mark.asyncio
    async def test_start_project_returns_early_if_already_running(self, proxy):
        existing_task = MagicMock()
        proxy._tasks["project-1"] = existing_task

        # If the lock path or create_task had been taken we would notice, redis is
        # None, but the _tasks check happens BEFORE the _redis check.
        await proxy.start_project("project-1", "session-1")

        # The task was not replaced.
        assert proxy._tasks["project-1"] is existing_task
        # Heartbeat was not started.
        assert "project-1" not in proxy._heartbeat_tasks

    @pytest.mark.asyncio
    async def test_start_project_idempotent_does_not_touch_redis(self, broker, admin_client):
        redis_mock = AsyncMock()
        proxy = Gns3WsProxy(
            broker=broker,
            gns3_url="http://gns3:3080",
            admin_client=admin_client,
            redis_url=None,
        )
        # Substitute the already initialized _redis field.
        proxy._redis = redis_mock
        proxy._tasks["project-1"] = MagicMock()

        await proxy.start_project("project-1", "session-1")

        # The lock was never requested, the early return kicked in.
        redis_mock.set.assert_not_called()


class TestStopAll:
    """stop_all cancels the tasks and heartbeats and awaits them."""

    @pytest.mark.asyncio
    async def test_stop_all_cancels_and_awaits_all_tasks(self, proxy):
        async def _sleep_forever():
            try:
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                raise

        task1 = asyncio.create_task(_sleep_forever())
        task2 = asyncio.create_task(_sleep_forever())
        hb1 = asyncio.create_task(_sleep_forever())
        hb2 = asyncio.create_task(_sleep_forever())

        proxy._tasks["p1"] = task1
        proxy._tasks["p2"] = task2
        proxy._heartbeat_tasks["p1"] = hb1
        proxy._heartbeat_tasks["p2"] = hb2

        await proxy.stop_all()

        assert task1.cancelled() or task1.done()
        assert task2.cancelled() or task2.done()
        assert hb1.cancelled() or hb1.done()
        assert hb2.cancelled() or hb2.done()
        assert proxy._tasks == {}
        assert proxy._heartbeat_tasks == {}

    @pytest.mark.asyncio
    async def test_stop_all_empty_state_is_noop(self, proxy):
        # It must not fail on empty dicts.
        await proxy.stop_all()
        assert proxy._tasks == {}
        assert proxy._heartbeat_tasks == {}

    @pytest.mark.asyncio
    async def test_stop_project_releases_redis_lock(self, broker, admin_client):
        proxy = Gns3WsProxy(
            broker=broker,
            gns3_url="http://gns3:3080",
            admin_client=admin_client,
            redis_url=None,
        )
        redis_mock = AsyncMock()
        proxy._redis = redis_mock

        await proxy.stop_project("project-1")

        # Released via CAS so we never delete a lock another instance took over.
        redis_mock.eval.assert_awaited_once()
        args = redis_mock.eval.await_args.args
        assert args[1] == 1
        assert args[2] == "lock:ws_proxy:project-1"
        assert args[3] == proxy._instance_id


class TestTranslate:
    """_translate converts a GNS3 event into a broker envelope."""

    def test_translate_node_updated_returns_status_changed(self, proxy):
        result = proxy._translate(
            "node.updated",
            {"node_id": "n1", "status": "started"},
        )
        assert result is not None
        assert result["type"] == "node.status_changed"
        assert result["payload"]["node_id"] == "n1"
        assert result["payload"]["status"] == "started"

    @pytest.mark.parametrize(
        "action", ["link.created", "link.deleted", "node.created", "node.deleted"]
    )
    def test_translate_returns_none_for_history_actions(self, proxy, action):
        # HistoryPgListener is the sole publisher of history.event; publishing here
        # too delivered every one of them twice.
        assert proxy._translate(action, {"link_id": "l1"}) is None

    def test_translate_unknown_action_returns_none(self, proxy):
        assert proxy._translate("unknown.action", {}) is None
