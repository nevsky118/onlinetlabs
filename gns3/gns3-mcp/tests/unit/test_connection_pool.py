"""ConnectionPool, LRU eviction, idle TTL, health check, backpressure.

Regression. The pool did not free slots and, after max_size UNIQUE users, stopped
handing out connections forever ("Connection pool exhausted"). In the 50-student
pilot the MCP server turned into a brick until restart.
"""

import mcp_sdk.connection as conn_mod
import pytest
from mcp_sdk.connection import ConnectionPool
from mcp_sdk.context import SessionContext
from mcp_sdk.errors import MCPServerError
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_in,
    assert_is_not_none,
    assert_less_equal,
    assert_true,
)

from tests.settings.data.connection_data import (
    CountingConnectionManagerData,
    FakeClockData,
)

pytestmark = [pytest.mark.unit, pytest.mark.connection]

GNS3_URL = "http://gns3-test:3080"


def _ctx(user_id: str, jwt: str | None = None) -> SessionContext:
    metadata = {"gns3_jwt": jwt} if jwt else {}
    return SessionContext(
        user_id=user_id,
        session_id=f"s-{user_id}",
        environment_url=GNS3_URL,
        metadata=metadata,
    )


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClockData()
    monkeypatch.setattr(conn_mod, "time", fake)
    return fake


class TestConnectionPool:
    @autotest.num("819")
    @autotest.external_id("a393b03d-2e5a-4479-b37c-af88997605ec")
    @autotest.name("ConnectionPool: a repeated request for the same user reuses the connection")
    async def test_a393b03d_reuses_connection_for_same_user(self, clock):
        with autotest.step("Arrange: manager and a pool with room for 5"):
            mgr = CountingConnectionManagerData()
            pool = ConnectionPool(manager=mgr, max_size=5)

        with autotest.step("Take a connection for the same user twice"):
            first = await pool.get_connection(_ctx("u1"))
            second = await pool.get_connection(_ctx("u1"))

        with autotest.step("Same connection, connect was called once"):
            assert_true(first is second, "first is second")
            assert_equal(mgr.connects, 1, "connects")
            assert_equal(pool.size, 1, "size")

    @autotest.num("820")
    @autotest.external_id("c52447e4-e48c-422d-9c0d-4f7fc7f9e329")
    @autotest.name("ConnectionPool: evicts LRU instead of raising when out of room")
    async def test_c52447e4_evicts_lru_instead_of_raising(self, clock):
        with autotest.step("Arrange: manager and a 2-slot pool with a short idle floor"):
            mgr = CountingConnectionManagerData()
            pool = ConnectionPool(manager=mgr, max_size=2, min_evict_idle=30.0)

        with autotest.step("Fill the pool with two users and let them go cold"):
            u1 = await pool.get_connection(_ctx("u1"))
            await pool.get_connection(_ctx("u2"))
            clock.advance(60.0)  # both connections are no longer "hot"

        with autotest.step("A third user gets a connection with no error"):
            third = await pool.get_connection(_ctx("u3"))
            assert_is_not_none(third, "third")

        with autotest.step("LRU (u1) was evicted, pool size stays within limit"):
            assert_equal(pool.size, 2, "size")
            assert_in(u1, mgr.disconnected, "u1")
            assert_equal(mgr.connects, 3, "connects")

    @autotest.num("821")
    @autotest.external_id("d84ce065-0784-4beb-801c-40b1270e20e4")
    @autotest.name("ConnectionPool: serves more unique users than max_size")
    async def test_d84ce065_survives_more_unique_users_than_max_size(self, clock):
        with autotest.step("Arrange: manager and a 3-slot pool with a short idle floor"):
            mgr = CountingConnectionManagerData()
            pool = ConnectionPool(manager=mgr, max_size=3, min_evict_idle=1.0)

        with autotest.step("Run 10 different users through a 3-slot pool"):
            for i in range(10):
                conn = await pool.get_connection(_ctx(f"u{i}"))
                assert_is_not_none(conn, "conn")
                clock.advance(5.0)  # the previous ones have time to cool down

        with autotest.step("Pool did not brick itself: size stays within max_size"):
            assert_less_equal(pool.size, 3, "size")
            assert_equal(mgr.connects, 10, "connects")

    @autotest.num("3492")
    @autotest.external_id("f981bc7a-942a-4444-bbdd-5a68731c6b8b")
    @autotest.name("ConnectionPool: closes connections idle longer than idle_ttl")
    async def test_f981bc7a_drops_idle_connections(self, clock):
        with autotest.step("Arrange: manager and a pool with a 100s idle TTL"):
            mgr = CountingConnectionManagerData()
            pool = ConnectionPool(manager=mgr, max_size=5, idle_ttl=100.0)

        with autotest.step("Take a connection and wait longer than idle_ttl"):
            stale = await pool.get_connection(_ctx("u1"))
            clock.advance(150.0)

        with autotest.step("Another user's request purges the stale connection"):
            await pool.get_connection(_ctx("u2"))
            assert_in(stale, mgr.disconnected, "stale")
            assert_equal(pool.size, 1, "size")

    @autotest.num("3493")
    @autotest.external_id("1d5d45cd-fcc2-477e-ad4c-e38392942ecf")
    @autotest.name("ConnectionPool: a dead connection is reopened on health-check")
    async def test_1d5d45cd_reconnects_dead_connection(self, clock):
        with autotest.step("Arrange: manager and a pool with a 10s health-check interval"):
            mgr = CountingConnectionManagerData()
            pool = ConnectionPool(manager=mgr, max_size=5, health_check_interval=10.0)

        with autotest.step("Take a connection, wait longer than health_check_interval"):
            dead = await pool.get_connection(_ctx("u1"))
            clock.advance(20.0)
            mgr.alive = False  # the connection died

        with autotest.step("The repeat request reopens the connection"):
            fresh = await pool.get_connection(_ctx("u1"))
            assert_true(fresh is not dead, "fresh is not dead")
            assert_in(dead, mgr.disconnected, "dead")
            assert_equal(mgr.connects, 2, "connects")

    @autotest.num("3494")
    @autotest.external_id("d0437fbb-b818-44e3-9dc2-b0385c987880")
    @autotest.name(
        "ConnectionPool: does not call health-check more often than health_check_interval"
    )
    async def test_d0437fbb_skips_health_check_within_interval(self, clock):
        with autotest.step("Arrange: manager and a pool with a 60s health-check interval"):
            mgr = CountingConnectionManagerData()
            pool = ConnectionPool(manager=mgr, max_size=5, health_check_interval=60.0)

        with autotest.step("Take a connection twice in a row"):
            await pool.get_connection(_ctx("u1"))
            await pool.get_connection(_ctx("u1"))

        with autotest.step("health_check was not called -- no extra round-trip"):
            assert_equal(mgr.health_calls, 0, "health calls")

    @autotest.num("825")
    @autotest.external_id("9d1fdb67-6aef-450e-b9de-ef0de67d6e52")
    @autotest.name("ConnectionPool: honest backpressure when ALL connections are hot")
    async def test_9d1fdb67_raises_when_all_connections_hot(self, clock):
        with autotest.step("Arrange: manager and a 2-slot pool with a long idle floor"):
            mgr = CountingConnectionManagerData()
            pool = ConnectionPool(manager=mgr, max_size=2, min_evict_idle=30.0)

        with autotest.step("Fill the pool with just-used connections"):
            await pool.get_connection(_ctx("u1"))
            await pool.get_connection(_ctx("u2"))

        with autotest.step("A third one fails: a live connection must not be torn down"):
            with pytest.raises(MCPServerError, match="exhausted"):
                await pool.get_connection(_ctx("u3"))

        with autotest.step("Live connections are untouched"):
            assert_equal(mgr.disconnected, [], "disconnected")
            assert_equal(pool.size, 2, "size")

    @autotest.num("826")
    @autotest.external_id("99c7fa94-23fc-47b7-a391-5ed69ad43938")
    @autotest.name("ConnectionPool.release: frees the user's slot")
    async def test_99c7fa94_release_frees_slot(self, clock):
        with autotest.step("Arrange: manager and a 1-slot pool"):
            mgr = CountingConnectionManagerData()
            pool = ConnectionPool(manager=mgr, max_size=1, min_evict_idle=30.0)

        with autotest.step("Occupy the only slot, then release it"):
            conn = await pool.get_connection(_ctx("u1"))
            await pool.release(_ctx("u1"))

        with autotest.step("Connection closed, slot free for another user"):
            assert_in(conn, mgr.disconnected, "conn")
            assert_equal(pool.size, 0, "size")
            other = await pool.get_connection(_ctx("u2"))
            assert_is_not_none(other, "other")
            assert_equal(pool.size, 1, "size")


class TestPoolKeyCredentialRotation:
    @autotest.num("862")
    @autotest.external_id("b1d7c2ea-5f43-4b6e-9a2c-7d1e8f0a4c33")
    @autotest.name("ConnectionPool: a rotated JWT does not reuse the stale connection")
    async def test_b1d7c2ea_rotated_jwt_gets_new_connection(self):
        with autotest.step("Arrange: pool over a manager that counts connects"):
            pool = ConnectionPool(manager=CountingConnectionManagerData())

        with autotest.step("Act: same user, same environment, rotated token"):
            first = await pool.get_connection(_ctx("u1", jwt="old-token"))
            second = await pool.get_connection(_ctx("u1", jwt="new-token"))

        with autotest.step("Assert: the stale client is not served again"):
            assert_true(first is not second, "first is not second")

    @autotest.num("863")
    @autotest.external_id("c4a2f8b9-3e17-4d55-8b0a-6f2c9d1e7a48")
    @autotest.name("ConnectionPool: an unchanged JWT reuses the connection")
    async def test_c4a2f8b9_same_jwt_reuses_connection(self):
        with autotest.step("Arrange: pool over a manager that counts connects"):
            pool = ConnectionPool(manager=CountingConnectionManagerData())

        with autotest.step("Act: same user, same token, twice"):
            first = await pool.get_connection(_ctx("u1", jwt="same-token"))
            second = await pool.get_connection(_ctx("u1", jwt="same-token"))

        with autotest.step("Assert: one connection is reused"):
            assert_true(first is second, "first is second")
