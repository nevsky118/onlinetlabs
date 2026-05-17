"""Unit-тесты Gns3WsProxy core поведения."""

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
    """Proxy без Redis — для большинства unit-тестов это корректно."""
    return Gns3WsProxy(
        broker=broker,
        gns3_url="http://gns3:3080",
        admin_client=admin_client,
        redis_url=None,
    )


class TestConstants:
    """Sanity-проверки констант."""

    def test_lock_ttl_seconds(self):
        assert Gns3WsProxy._LOCK_TTL_SECONDS == 3600

    def test_heartbeat_interval_seconds(self):
        assert Gns3WsProxy._HEARTBEAT_INTERVAL_SECONDS == 1800


class TestBackoffDelay:
    """Экспоненциальный backoff: 1, 2, 4, 8, 16, 30, 30 для attempts 0-6."""

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
    """Формат ключа Redis-лока."""

    def test_lock_key_format(self, proxy):
        assert proxy._lock_key("project-123") == "lock:ws_proxy:project-123"

    def test_lock_key_with_uuid(self, proxy):
        pid = "11111111-1111-1111-1111-111111111111"
        assert proxy._lock_key(pid) == f"lock:ws_proxy:{pid}"


class TestStartProjectIdempotency:
    """start_project — идемпотентность при наличии задачи."""

    @pytest.mark.asyncio
    async def test_start_project_returns_early_if_already_running(self, proxy):
        existing_task = MagicMock()
        proxy._tasks["project-1"] = existing_task

        # Если бы пошёл лок-путь или create_task, мы бы заметили: redis None,
        # но проверка _tasks происходит ДО проверки _redis.
        await proxy.start_project("project-1", "session-1")

        # Задача не была заменена.
        assert proxy._tasks["project-1"] is existing_task
        # Heartbeat не запускался.
        assert "project-1" not in proxy._heartbeat_tasks

    @pytest.mark.asyncio
    async def test_start_project_idempotent_does_not_touch_redis(
        self, broker, admin_client
    ):
        redis_mock = AsyncMock()
        proxy = Gns3WsProxy(
            broker=broker,
            gns3_url="http://gns3:3080",
            admin_client=admin_client,
            redis_url=None,
        )
        # Подменяем уже инициализированное поле _redis.
        proxy._redis = redis_mock
        proxy._tasks["project-1"] = MagicMock()

        await proxy.start_project("project-1", "session-1")

        # Лок не запрашивался — ранний return сработал.
        redis_mock.set.assert_not_called()


class TestStopAll:
    """stop_all — отменяет таски и heartbeat и ожидает их."""

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
        # Не должно падать на пустых словарях.
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

        redis_mock.delete.assert_awaited_once_with("lock:ws_proxy:project-1")


class TestTranslate:
    """_translate — преобразование GNS3 event → broker envelope."""

    def test_translate_node_updated_returns_status_changed(self, proxy):
        result = proxy._translate(
            "node.updated",
            {"node_id": "n1", "status": "started"},
        )
        assert result is not None
        assert result["type"] == "node.status_changed"
        assert result["payload"]["node_id"] == "n1"
        assert result["payload"]["status"] == "started"

    def test_translate_link_created_returns_history_event(self, proxy):
        result = proxy._translate("link.created", {"link_id": "l1"})
        assert result is not None
        assert result["type"] == "history.event"
        assert result["payload"]["event_type"] == "link.created"
        assert result["payload"]["component_id"] == "l1"

    def test_translate_unknown_action_returns_none(self, proxy):
        assert proxy._translate("unknown.action", {}) is None
