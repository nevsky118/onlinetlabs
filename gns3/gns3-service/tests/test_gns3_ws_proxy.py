"""Unit tests for the core Gns3WsProxy behavior."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_sdk.testing import autotest

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

    @autotest.num("3327")
    @autotest.external_id("c1d6af9b-ec2e-4423-918e-1714077f469a")
    @autotest.name("Gns3WsProxy: lock TTL constant is 90 seconds")
    def test_c1d6af9b_lock_ttl_seconds(self):
        with autotest.step("Assert: the lock TTL constant is 90 seconds"):
            assert Gns3WsProxy._LOCK_TTL_SECONDS == 90

    @autotest.num("3328")
    @autotest.external_id("351f19ac-f77f-423b-8719-c929919eba8f")
    @autotest.name("Gns3WsProxy: heartbeat interval constant is 30 seconds")
    def test_351f19ac_heartbeat_interval_seconds(self):
        with autotest.step("Assert: the heartbeat interval constant is 30 seconds"):
            assert Gns3WsProxy._HEARTBEAT_INTERVAL_SECONDS == 30

    @autotest.num("3329")
    @autotest.external_id("92f7c7ba-161b-4931-8230-987d2d536bfc")
    @autotest.name("Gns3WsProxy: heartbeat interval leaves margin inside the lock TTL")
    def test_92f7c7ba_heartbeat_runs_well_inside_the_ttl(self):
        with autotest.step("Assert: the heartbeat interval leaves margin inside the lock TTL"):
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
    @autotest.num("3330")
    @autotest.external_id("eebc1d79-ad00-4290-a6fd-c4bcf179c403")
    @autotest.name("Gns3WsProxy._backoff_delay: matches the expected exponential sequence")
    def test_eebc1d79_backoff_delay_sequence(self, proxy, attempt, expected):
        with autotest.step("Act + Assert: the backoff delay matches the expected sequence"):
            assert proxy._backoff_delay(attempt) == expected


class TestLockKey:
    """Format of the Redis lock key."""

    @autotest.num("3331")
    @autotest.external_id("aea60eaa-fc3c-4f83-a4d9-573c2aa857bb")
    @autotest.name("Gns3WsProxy._lock_key: namespaced with the project id")
    def test_aea60eaa_lock_key_format(self, proxy):
        with autotest.step("Act + Assert: the lock key is namespaced with the project id"):
            assert proxy._lock_key("project-123") == "lock:ws_proxy:project-123"

    @autotest.num("3332")
    @autotest.external_id("57efad01-d1c2-4a9c-b043-78facbdcdff3")
    @autotest.name("Gns3WsProxy._lock_key: namespaced with a UUID project id")
    def test_57efad01_lock_key_with_uuid(self, proxy):
        with autotest.step("Arrange: a UUID-shaped project id"):
            pid = "11111111-1111-1111-1111-111111111111"

        with autotest.step("Act + Assert: the lock key is namespaced with the UUID"):
            assert proxy._lock_key(pid) == f"lock:ws_proxy:{pid}"


class TestStartProjectIdempotency:
    """start_project is idempotent when a task already exists."""

    @pytest.mark.asyncio
    @autotest.num("3333")
    @autotest.external_id("82792b72-477e-40c8-9a41-4047a60c4f47")
    @autotest.name("Gns3WsProxy.start_project: returns early when a task is already running")
    async def test_82792b72_start_project_returns_early_if_already_running(self, proxy):
        with autotest.step("Arrange: seed an already-running task for the project"):
            existing_task = MagicMock()
            proxy._tasks["project-1"] = existing_task

        with autotest.step("Act: start the same project again"):
            # If the lock path or create_task had been taken we would notice, redis is
            # None, but the _tasks check happens BEFORE the _redis check.
            await proxy.start_project("project-1", "session-1")

        with autotest.step("Assert: the existing task and heartbeat state are untouched"):
            # The task was not replaced.
            assert proxy._tasks["project-1"] is existing_task
            # Heartbeat was not started.
            assert "project-1" not in proxy._heartbeat_tasks

    @pytest.mark.asyncio
    @autotest.num("3334")
    @autotest.external_id("32e1bc17-1a6b-4705-a4e6-03ddf862e99d")
    @autotest.name("Gns3WsProxy.start_project: idempotent restart never touches redis")
    async def test_32e1bc17_start_project_idempotent_does_not_touch_redis(
        self, broker, admin_client
    ):
        with autotest.step("Arrange: a proxy with mocked redis and an already-running task"):
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

        with autotest.step("Act: start the same project again"):
            await proxy.start_project("project-1", "session-1")

        with autotest.step("Assert: redis is never touched, the early return kicked in"):
            # The lock was never requested, the early return kicked in.
            redis_mock.set.assert_not_called()


class TestStopAll:
    """stop_all cancels the tasks and heartbeats and awaits them."""

    @pytest.mark.asyncio
    @autotest.num("3335")
    @autotest.external_id("97996d7b-9773-4c77-932f-609bc120a713")
    @autotest.name("Gns3WsProxy.stop_all: cancels and awaits every task and heartbeat")
    async def test_97996d7b_stop_all_cancels_and_awaits_all_tasks(self, proxy):
        with autotest.step("Arrange: register two running tasks and two heartbeat tasks"):

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

        with autotest.step("Act: stop all projects"):
            await proxy.stop_all()

        with autotest.step("Assert: every task and heartbeat is cancelled, state is cleared"):
            assert task1.cancelled() or task1.done()
            assert task2.cancelled() or task2.done()
            assert hb1.cancelled() or hb1.done()
            assert hb2.cancelled() or hb2.done()
            assert proxy._tasks == {}
            assert proxy._heartbeat_tasks == {}

    @pytest.mark.asyncio
    @autotest.num("3336")
    @autotest.external_id("b7fa99ac-742c-4842-b2ff-dea2cc62e048")
    @autotest.name("Gns3WsProxy.stop_all: is a no-op with no running tasks")
    async def test_b7fa99ac_stop_all_empty_state_is_noop(self, proxy):
        with autotest.step("Act: stop all projects with no running tasks"):
            # It must not fail on empty dicts.
            await proxy.stop_all()

        with autotest.step("Assert: the task and heartbeat state remain empty"):
            assert proxy._tasks == {}
            assert proxy._heartbeat_tasks == {}

    @pytest.mark.asyncio
    @autotest.num("3337")
    @autotest.external_id("94a07610-fdc9-4be3-a9b9-94e519e5f30d")
    @autotest.name("Gns3WsProxy.stop_project: releases the redis lock via CAS")
    async def test_94a07610_stop_project_releases_redis_lock(self, broker, admin_client):
        with autotest.step("Arrange: a proxy with a mocked redis client"):
            proxy = Gns3WsProxy(
                broker=broker,
                gns3_url="http://gns3:3080",
                admin_client=admin_client,
                redis_url=None,
            )
            redis_mock = AsyncMock()
            proxy._redis = redis_mock

        with autotest.step("Act: stop the project"):
            await proxy.stop_project("project-1")

        with autotest.step("Assert: the lock is released via CAS with this instance's id"):
            # Released via CAS so we never delete a lock another instance took over.
            redis_mock.eval.assert_awaited_once()
            args = redis_mock.eval.await_args.args
            assert args[1] == 1
            assert args[2] == "lock:ws_proxy:project-1"
            assert args[3] == proxy._instance_id


class TestTranslate:
    """_translate converts a GNS3 event into a broker envelope."""

    @autotest.num("3338")
    @autotest.external_id("27119a1c-1c98-41b2-a372-75950dadd477")
    @autotest.name("Gns3WsProxy._translate: node.updated becomes node.status_changed")
    def test_27119a1c_translate_node_updated_returns_status_changed(self, proxy):
        with autotest.step("Act: translate a node.updated GNS3 event"):
            result = proxy._translate(
                "node.updated",
                {"node_id": "n1", "status": "started"},
            )

        with autotest.step("Assert: it becomes a node.status_changed envelope"):
            assert result is not None
            assert result["type"] == "node.status_changed"
            assert result["payload"]["node_id"] == "n1"
            assert result["payload"]["status"] == "started"

    @pytest.mark.parametrize(
        "action", ["link.created", "link.deleted", "node.created", "node.deleted"]
    )
    @autotest.num("3339")
    @autotest.external_id("ab52175a-7acc-47d1-8c19-bd3d9ddd8db5")
    @autotest.name("Gns3WsProxy._translate: history-owned actions translate to None")
    def test_ab52175a_translate_returns_none_for_history_actions(self, proxy, action):
        with autotest.step("Act + Assert: history-owned actions translate to None"):
            # HistoryPgListener is the sole publisher of history.event; publishing here
            # too delivered every one of them twice.
            assert proxy._translate(action, {"link_id": "l1"}) is None

    @autotest.num("3340")
    @autotest.external_id("434abd72-d552-4f1e-a5c5-142dc98a131d")
    @autotest.name("Gns3WsProxy._translate: an unknown action translates to None")
    def test_434abd72_translate_unknown_action_returns_none(self, proxy):
        with autotest.step("Act + Assert: an unknown action translates to None"):
            assert proxy._translate("unknown.action", {}) is None
