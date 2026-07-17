"""ConnectionPool: LRU-вытеснение, idle-TTL, health-check, backpressure.

Регрессия: пул не освобождал слоты и после max_size УНИКАЛЬНЫХ пользователей
навсегда переставал выдавать соединения («Connection pool exhausted») — на пилоте
в 50 студентов MCP-сервер становился кирпичом до рестарта.
"""

import mcp_sdk.connection as conn_mod
import pytest
from mcp_sdk.connection import BaseConnectionManager, ConnectionPool
from mcp_sdk.context import SessionContext
from mcp_sdk.errors import MCPServerError
from mcp_sdk.testing import autotest

pytestmark = [pytest.mark.unit, pytest.mark.connection]

GNS3_URL = "http://gns3-test:3080"


def _ctx(user_id: str) -> SessionContext:
    return SessionContext(user_id=user_id, session_id=f"s-{user_id}", environment_url=GNS3_URL)


class _FakeTime:
    """Управляемые часы: подменяют модуль time внутри mcp_sdk.connection."""

    def __init__(self) -> None:
        self._t = 1000.0

    def monotonic(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds


class _FakeManager(BaseConnectionManager):
    def __init__(self, alive: bool = True) -> None:
        self.connects = 0
        self.disconnected: list = []
        self.health_calls = 0
        self.alive = alive

    async def connect(self, ctx: SessionContext):
        self.connects += 1
        return {"id": f"conn-{self.connects}", "user": ctx.user_id}

    async def disconnect(self, connection) -> None:
        self.disconnected.append(connection)

    async def health_check(self, connection) -> bool:
        self.health_calls += 1
        return self.alive


@pytest.fixture
def clock(monkeypatch):
    fake = _FakeTime()
    monkeypatch.setattr(conn_mod, "time", fake)
    return fake


class TestConnectionPool:
    @autotest.num("819")
    @autotest.external_id("a393b03d-2e5a-4479-b37c-af88997605ec")
    @autotest.name("ConnectionPool: повторный запрос того же юзера переиспользует соединение")
    async def test_a393b03d_reuses_connection_for_same_user(self, clock):
        mgr = _FakeManager()
        pool = ConnectionPool(manager=mgr, max_size=5)

        with autotest.step("Дважды берём соединение одного пользователя"):
            first = await pool.get_connection(_ctx("u1"))
            second = await pool.get_connection(_ctx("u1"))

        with autotest.step("Соединение то же, connect был один раз"):
            assert first is second
            assert mgr.connects == 1
            assert pool.size == 1

    @autotest.num("820")
    @autotest.external_id("c52447e4-e48c-422d-9c0d-4f7fc7f9e329")
    @autotest.name("ConnectionPool: при нехватке места вытесняет LRU, а не падает")
    async def test_c52447e4_evicts_lru_instead_of_raising(self, clock):
        mgr = _FakeManager()
        pool = ConnectionPool(manager=mgr, max_size=2, min_evict_idle=30.0)

        with autotest.step("Заполняем пул двумя пользователями и даём им остыть"):
            u1 = await pool.get_connection(_ctx("u1"))
            await pool.get_connection(_ctx("u2"))
            clock.advance(60.0)  # оба соединения перестали быть «горячими»

        with autotest.step("Третий пользователь получает соединение без ошибки"):
            third = await pool.get_connection(_ctx("u3"))
            assert third is not None

        with autotest.step("Вытеснен LRU (u1), размер пула не превышен"):
            assert pool.size == 2
            assert u1 in mgr.disconnected
            assert mgr.connects == 3

    @autotest.num("821")
    @autotest.external_id("d84ce065-0784-4beb-801c-40b1270e20e4")
    @autotest.name("ConnectionPool: обслуживает больше уникальных юзеров, чем max_size")
    async def test_d84ce065_survives_more_unique_users_than_max_size(self, clock):
        mgr = _FakeManager()
        pool = ConnectionPool(manager=mgr, max_size=3, min_evict_idle=1.0)

        with autotest.step("Прогоняем 10 разных пользователей через пул на 3 слота"):
            for i in range(10):
                conn = await pool.get_connection(_ctx(f"u{i}"))
                assert conn is not None
                clock.advance(5.0)  # предыдущие успевают остыть

        with autotest.step("Пул не «закирпичился»: размер в пределах max_size"):
            assert pool.size <= 3
            assert mgr.connects == 10

    @autotest.num("822")
    @autotest.external_id("f981bc7a-942a-4444-bbdd-5a68731c6b8b")
    @autotest.name("ConnectionPool: закрывает соединения, простаивающие дольше idle_ttl")
    async def test_f981bc7a_drops_idle_connections(self, clock):
        mgr = _FakeManager()
        pool = ConnectionPool(manager=mgr, max_size=5, idle_ttl=100.0)

        with autotest.step("Берём соединение и ждём дольше idle_ttl"):
            stale = await pool.get_connection(_ctx("u1"))
            clock.advance(150.0)

        with autotest.step("Обращение другого юзера вычищает протухшее"):
            await pool.get_connection(_ctx("u2"))
            assert stale in mgr.disconnected
            assert pool.size == 1

    @autotest.num("823")
    @autotest.external_id("1d5d45cd-fcc2-477e-ad4c-e38392942ecf")
    @autotest.name("ConnectionPool: мёртвое соединение переоткрывается по health-check")
    async def test_1d5d45cd_reconnects_dead_connection(self, clock):
        mgr = _FakeManager()
        pool = ConnectionPool(manager=mgr, max_size=5, health_check_interval=10.0)

        with autotest.step("Берём соединение, ждём дольше health_check_interval"):
            dead = await pool.get_connection(_ctx("u1"))
            clock.advance(20.0)
            mgr.alive = False  # соединение умерло

        with autotest.step("Повторный запрос переоткрывает соединение"):
            fresh = await pool.get_connection(_ctx("u1"))
            assert fresh is not dead
            assert dead in mgr.disconnected
            assert mgr.connects == 2

    @autotest.num("824")
    @autotest.external_id("d0437fbb-b818-44e3-9dc2-b0385c987880")
    @autotest.name("ConnectionPool: не дёргает health-check чаще health_check_interval")
    async def test_d0437fbb_skips_health_check_within_interval(self, clock):
        mgr = _FakeManager()
        pool = ConnectionPool(manager=mgr, max_size=5, health_check_interval=60.0)

        with autotest.step("Берём соединение дважды подряд"):
            await pool.get_connection(_ctx("u1"))
            await pool.get_connection(_ctx("u1"))

        with autotest.step("health_check не вызывался — лишнего round-trip нет"):
            assert mgr.health_calls == 0

    @autotest.num("825")
    @autotest.external_id("9d1fdb67-6aef-450e-b9de-ef0de67d6e52")
    @autotest.name("ConnectionPool: если ВСЕ соединения активны — честный backpressure")
    async def test_9d1fdb67_raises_when_all_connections_hot(self, clock):
        mgr = _FakeManager()
        pool = ConnectionPool(manager=mgr, max_size=2, min_evict_idle=30.0)

        with autotest.step("Заполняем пул только что использованными соединениями"):
            await pool.get_connection(_ctx("u1"))
            await pool.get_connection(_ctx("u2"))

        with autotest.step("Третий падает: рвать живое соединение нельзя"):
            with pytest.raises(MCPServerError, match="exhausted"):
                await pool.get_connection(_ctx("u3"))

        with autotest.step("Живые соединения не тронуты"):
            assert mgr.disconnected == []
            assert pool.size == 2

    @autotest.num("826")
    @autotest.external_id("99c7fa94-23fc-47b7-a391-5ed69ad43938")
    @autotest.name("ConnectionPool.release: освобождает слот пользователя")
    async def test_99c7fa94_release_frees_slot(self, clock):
        mgr = _FakeManager()
        pool = ConnectionPool(manager=mgr, max_size=1, min_evict_idle=30.0)

        with autotest.step("Занимаем единственный слот и освобождаем его"):
            conn = await pool.get_connection(_ctx("u1"))
            await pool.release(_ctx("u1"))

        with autotest.step("Соединение закрыто, слот свободен для другого юзера"):
            assert conn in mgr.disconnected
            assert pool.size == 0
            other = await pool.get_connection(_ctx("u2"))
            assert other is not None
            assert pool.size == 1
