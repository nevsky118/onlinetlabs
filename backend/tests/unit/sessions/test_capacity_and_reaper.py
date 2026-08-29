"""Queue bookkeeping, the session deadline, and the caller the rate limiter sees."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.session import LearningSession
from models.user import User
from rate_limit import client_ip
from sessions.queue import SessionQueueService
from sessions.reaper import reap_expired_sessions
from tests.settings.data.queue_data import FakeRedisData, ForwardedHeaderData

pytestmark = [pytest.mark.unit]

_OWNER = "user-cap-1"
_LAB = "lan-static-ip"


def _service() -> SessionQueueService:
    """A queue service backed by an in-memory redis double."""
    service = SessionQueueService.__new__(SessionQueueService)
    service._redis = FakeRedisData()
    return service


class TestQueueBookkeeping:
    """A polling client must not be able to grow the queue."""

    @autotest.num("3426")
    @autotest.external_id("df21b81e-8e14-48b0-b260-03b830ee3659")
    @autotest.name("queue: repeated enqueues keep one entry and one position")
    async def test_df21b81e_enqueue_is_idempotent(self):
        with autotest.step("Arrange: one waiting learner"):
            queue = _service()

        with autotest.step("Act: enqueue five times, as a 5-second poll would"):
            positions = [await queue.enqueue(_OWNER, _LAB) for _ in range(5)]

        with autotest.step("Assert: one entry, position stable at 1"):
            assert_equal(await queue.queue_depth(_LAB), 1, "one entry")
            assert_equal(positions, [1, 1, 1, 1, 1], "position stable")

    @autotest.num("3427")
    @autotest.external_id("c6fbb855-576d-476e-a424-bc69669514f7")
    @autotest.name("queue: order is preserved across different learners")
    async def test_c6fbb855_order_preserved(self):
        with autotest.step("Arrange: three learners join in order"):
            queue = _service()
            first = await queue.enqueue("u1", _LAB)
            second = await queue.enqueue("u2", _LAB)
            third = await queue.enqueue("u3", _LAB)

        with autotest.step("Act: re-poll as the middle learner"):
            repoll = await queue.enqueue("u2", _LAB)

        with autotest.step("Assert: positions are 1, 2, 3 and the re-poll does not move anyone"):
            assert_equal([first, second, third], [1, 2, 3], "join order")
            assert_equal(repoll, 2, "position unchanged")
            assert_equal(await queue.queue_depth(_LAB), 3, "three waiters")

    @autotest.num("3428")
    @autotest.external_id("0ccad3cb-b799-4dd7-af97-0d000416d494")
    @autotest.name("queue: acquiring a slot removes the learner from the queue")
    async def test_0ccad3cb_acquire_dequeues(self):
        with autotest.step("Arrange: a waiting learner"):
            queue = _service()
            await queue.enqueue(_OWNER, _LAB)

        with autotest.step("Act: a slot frees up and the learner acquires it"):
            acquired = await queue.try_acquire(_OWNER, _LAB)

        with autotest.step("Assert: they are no longer queued"):
            assert_true(acquired, "slot acquired")
            assert_equal(await queue.queue_depth(_LAB), 0, "queue emptied")
            assert_true(await queue.position(_OWNER, _LAB) is None, "no position")

    @autotest.num("3429")
    @autotest.external_id("fe7ab768-f5cc-4859-8b37-ddae67c8592f")
    @autotest.name("queue: the queue key carries an expiry")
    async def test_fe7ab768_queue_key_expires(self):
        with autotest.step("Arrange: a waiting learner"):
            queue = _service()
            await queue.enqueue(_OWNER, _LAB)

        with autotest.step("Act: read the key's ttl"):
            ttl = queue._redis.ttls.get(f"queue:{_LAB}")

        with autotest.step("Assert: an expiry was set"):
            assert_true(ttl is not None and ttl > 0, "queue key expires")

    @autotest.num("3430")
    @autotest.external_id("db960ab1-8358-4177-87b4-5445acd6d1b5")
    @autotest.name("queue: the ETA comes from observed provisioning, not a constant")
    async def test_db960ab1_eta_from_observation(self):
        with autotest.step("Arrange: three recorded provisioning durations"):
            queue = _service()
            for seconds in (10.0, 20.0, 60.0):
                await queue.record_provision_seconds(seconds)

        with autotest.step("Act: read the average"):
            average = await queue.avg_provision_seconds()

        with autotest.step("Assert: the mean of what was observed"):
            assert_equal(average, 30.0, "mean of samples")

    @autotest.num("3431")
    @autotest.external_id("76c6deec-5dae-48a2-9cf6-474bb6f5811f")
    @autotest.name("queue: with no samples the ETA falls back rather than dividing by zero")
    async def test_76c6deec_eta_fallback(self):
        with autotest.step("Arrange: a queue that has never provisioned"):
            queue = _service()

        with autotest.step("Act: read the average"):
            average = await queue.avg_provision_seconds()

        with autotest.step("Assert: the documented fallback"):
            assert_equal(average, 30.0, "fallback")


class TestSessionReaper:
    """Nothing but the deadline should be able to end a session on its own."""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)
        with patch("sessions.reaper.async_session", self.session_factory):
            yield
        await self.engine.dispose()

    async def _seed(self, session_id: str, expires_at: datetime | None) -> None:
        """Inserts one active session with the given deadline."""
        async with self.session_factory() as db:
            db.add(
                LearningSession(
                    id=session_id,
                    user_id=_OWNER,
                    lab_slug=_LAB,
                    status="active",
                    expires_at=expires_at,
                    meta={"gns3_service_session_id": f"gns3-{session_id}"},
                )
            )
            await db.commit()

    def _deps(self):
        """A gns3 client and a monitor registry that record what the reaper did."""
        gns3 = AsyncMock()
        gns3.delete_session = AsyncMock(return_value=True)
        registry = MagicMock()
        registry.stop = AsyncMock()
        return gns3, registry

    @autotest.num("3432")
    @autotest.external_id("02fe1b05-a2f6-4429-96bb-4ff7aac1c461")
    @autotest.name("reaper: a session past its deadline is ended and torn down")
    async def test_02fe1b05_expired_is_ended(self):
        with autotest.step("Arrange: a session whose deadline has passed"):
            await self._seed("sess-old", datetime.now(UTC) - timedelta(hours=1))
            gns3, registry = self._deps()

        with autotest.step("Act: run one reap pass"):
            with patch("sessions.reaper.persist_volatile_configs", AsyncMock(return_value=1)):
                ended = await reap_expired_sessions(gns3, registry)

        with autotest.step("Assert: ended, monitor stopped, gns3 session deleted"):
            assert_equal(ended, 1, "one ended")
            registry.stop.assert_awaited_once()
            gns3.delete_session.assert_awaited_once()
            async with self.session_factory() as db:
                row = await db.get(LearningSession, "sess-old")
            assert_equal(row.status, "ended", "status ended")
            assert_true(row.ended_at is not None, "ended_at set")

    @autotest.num("3433")
    @autotest.external_id("74a8d77a-9768-40e5-8b9e-4f04a3cf7079")
    @autotest.name("reaper: a session inside its deadline is left alone")
    async def test_74a8d77a_live_session_survives(self):
        with autotest.step("Arrange: a session with hours left"):
            await self._seed("sess-live", datetime.now(UTC) + timedelta(hours=6))
            gns3, registry = self._deps()

        with autotest.step("Act: run one reap pass"):
            with patch("sessions.reaper.persist_volatile_configs", AsyncMock(return_value=0)):
                ended = await reap_expired_sessions(gns3, registry)

        with autotest.step("Assert: untouched"):
            assert_equal(ended, 0, "none ended")
            gns3.delete_session.assert_not_awaited()


class TestClientAddress:
    """The rate limiter must see the caller, not the reverse proxy."""

    @autotest.num("3434")
    @autotest.external_id("df21b81e-8e14-48b0-b260-03b830ee3660")
    @autotest.name("client_ip: the proxy-appended entry wins over a spoofed one")
    def test_df21b81e_spoofed_prefix_ignored(self):
        with autotest.step("Arrange: a client that put its own value in the header"):
            data = ForwardedHeaderData.spoofed()

        with autotest.step("Act: resolve the caller"):
            resolved = client_ip(
                SimpleNamespace(headers={"x-forwarded-for": data.header}, client=None)
            )

        with autotest.step("Assert: the address the proxy appended"):
            assert_equal(resolved, data.expected, "real peer")

    @autotest.num("3435")
    @autotest.external_id("c6fbb855-576d-476e-a424-bc69669514f8")
    @autotest.name("client_ip: two callers behind the proxy get different keys")
    def test_c6fbb855_distinct_callers(self):
        with autotest.step("Arrange: two requests through the same proxy"):
            first, second = ForwardedHeaderData.two_callers()

        with autotest.step("Act: resolve both"):
            a = client_ip(SimpleNamespace(headers={"x-forwarded-for": first.header}, client=None))
            b = client_ip(SimpleNamespace(headers={"x-forwarded-for": second.header}, client=None))

        with autotest.step("Assert: independent buckets"):
            assert_true(a != b, "different keys")
            assert_equal(a, first.expected, "first caller")
            assert_equal(b, second.expected, "second caller")
