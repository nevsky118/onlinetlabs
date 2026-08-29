"""Idle reclaim: what counts as activity, and that a pause never destroys work."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.identity import User
from models.learning import LearningSession
from sessions.activity import TOUCH_THROTTLE_SEC, touch_session
from tests.settings.data.vpcs_data import Gns3NodeStateData
from worker.idle_reclaim import IDLE_THRESHOLD_MIN, _reclaim_idle_sessions

pytestmark = [pytest.mark.unit]

_OWNER = "user-reclaim-1"
_STRANGER = "user-reclaim-2"


def _stale() -> datetime:
    """A last_seen_at old enough to be reclaimed."""
    return datetime.now(UTC) - timedelta(minutes=IDLE_THRESHOLD_MIN + 5)


def _fresh() -> datetime:
    """A last_seen_at inside the idle threshold."""
    return datetime.now(UTC) - timedelta(minutes=1)


def _utc(value: datetime | None) -> datetime | None:
    """sqlite drops tzinfo on read; postgres does not."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


class TestTouchSession:
    """last_seen_at stamping: throttled, and scoped to the owner."""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)
        yield
        await self.engine.dispose()

    async def _seed(self, last_seen: datetime) -> str:
        """Inserts one active session owned by _OWNER."""
        async with self.session_factory() as db:
            row = LearningSession(
                id="sess-touch",
                user_id=_OWNER,
                lab_slug="lan-static-ip",
                status="active",
                last_seen_at=last_seen,
            )
            db.add(row)
            await db.commit()
        return "sess-touch"

    async def _last_seen(self, session_id: str) -> datetime:
        """Reads back the stamp."""
        async with self.session_factory() as db:
            row = await db.get(LearningSession, session_id)
            return _utc(row.last_seen_at)

    @autotest.num("3399")
    @autotest.external_id("2a3778b0-01cf-45d0-930e-fc20afcd9c4b")
    @autotest.name("touch_session: a stale stamp is advanced")
    async def test_2a3778b0_stale_stamp_advances(self):
        with autotest.step("Arrange: a session last seen well outside the throttle window"):
            before = _stale()
            session_id = await self._seed(before)

        with autotest.step("Act: touch it as its owner"):
            async with self.session_factory() as db:
                await touch_session(db, session_id, _OWNER)

        with autotest.step("Assert: last_seen_at moved forward"):
            after = await self._last_seen(session_id)
            assert_true(after > before, "stamp advanced")

    @autotest.num("3400")
    @autotest.external_id("fd90c42f-4a44-4a02-8bba-1a9936edf557")
    @autotest.name("touch_session: a fresh stamp is left alone")
    async def test_fd90c42f_fresh_stamp_is_throttled(self):
        with autotest.step("Arrange: a session touched inside the throttle window"):
            before = datetime.now(UTC) - timedelta(seconds=TOUCH_THROTTLE_SEC // 2)
            session_id = await self._seed(before)

        with autotest.step("Act: touch it again"):
            async with self.session_factory() as db:
                await touch_session(db, session_id, _OWNER)

        with autotest.step("Assert: no write happened"):
            after = await self._last_seen(session_id)
            assert_equal(after, before, "stamp unchanged")

    @autotest.num("3401")
    @autotest.external_id("85a2beba-2e20-4833-842d-335f115d5606")
    @autotest.name("touch_session: a stranger cannot keep someone else's session alive")
    async def test_85a2beba_stranger_cannot_stamp(self):
        with autotest.step("Arrange: a stale session owned by someone else"):
            before = _stale()
            session_id = await self._seed(before)

        with autotest.step("Act: touch it as a different user"):
            async with self.session_factory() as db:
                await touch_session(db, session_id, _STRANGER)

        with autotest.step("Assert: the stamp did not move"):
            after = await self._last_seen(session_id)
            assert_equal(after, before, "stamp unchanged")


class TestReclaimIdleSessions:
    """Which sessions are reclaimed, and what happens to them when they are."""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)
        with patch("worker.idle_reclaim.async_session", self.session_factory):
            yield
        await self.engine.dispose()

    async def _seed(
        self,
        session_id: str,
        last_seen: datetime,
        paused_at: datetime | None = None,
        status: str = "active",
    ) -> None:
        """Inserts one session with the given liveness."""
        async with self.session_factory() as db:
            db.add(
                LearningSession(
                    id=session_id,
                    user_id=_OWNER,
                    lab_slug="lan-static-ip",
                    status=status,
                    last_seen_at=last_seen,
                    paused_at=paused_at,
                    meta={"gns3_service_session_id": f"gns3-{session_id}"},
                )
            )
            await db.commit()

    def _client(self, activity_ts: str | None = None) -> AsyncMock:
        """A gns3 client whose activity feed carries at most one event."""
        client = AsyncMock()
        events = [{"timestamp": activity_ts}] if activity_ts else []
        client.get_activity = AsyncMock(return_value={"events": events})
        client.bulk_node_action = AsyncMock(return_value=True)
        return client

    async def _paused_at(self, session_id: str) -> datetime | None:
        """Reads back the pause marker."""
        async with self.session_factory() as db:
            row = await db.get(LearningSession, session_id)
            return _utc(row.paused_at)

    @autotest.num("3402")
    @autotest.external_id("e49fb50e-6d87-4901-9740-864953d7dd02")
    @autotest.name("reclaim: a session working at the console is not reclaimed")
    async def test_e49fb50e_recent_activity_is_spared(self):
        with autotest.step("Arrange: last_seen_at inside the threshold, no gns3 events"):
            await self._seed("sess-fresh", _fresh())
            client = self._client()

        with autotest.step("Act: run one reclaim pass"):
            with patch("worker.idle_reclaim.persist_volatile_configs", AsyncMock(return_value=2)):
                await _reclaim_idle_sessions(client)

        with autotest.step("Assert: nodes were never stopped and the session is not paused"):
            assert_equal(client.bulk_node_action.await_count, 0, "no stop")
            assert_true(await self._paused_at("sess-fresh") is None, "not paused")

    @autotest.num("3403")
    @autotest.external_id("c51bcc0b-a61b-4e07-9694-3ffa25100afc")
    @autotest.name("reclaim: config is saved before the nodes are stopped")
    async def test_c51bcc0b_saves_before_stop(self):
        with autotest.step("Arrange: an idle session"):
            await self._seed("sess-idle", _stale())
            client = self._client()
            calls: list[str] = []

        with autotest.step("Act: run one reclaim pass, recording the call order"):

            async def _persist(*_args, **_kwargs):
                calls.append("save")
                return 2

            async def _stop(*_args, **_kwargs):
                calls.append("stop")
                return True

            client.bulk_node_action = AsyncMock(side_effect=_stop)
            with patch("worker.idle_reclaim.persist_volatile_configs", _persist):
                await _reclaim_idle_sessions(client)

        with autotest.step("Assert: the save happened first"):
            assert_equal(calls, ["save", "stop"], "save precedes stop")

    @autotest.num("3404")
    @autotest.external_id("a0a8b98b-2a44-45e2-b4b3-d23e63d0b9e7")
    @autotest.name("reclaim: a reclaimed session is marked paused, not left broken")
    async def test_a0a8b98b_marks_paused(self):
        with autotest.step("Arrange: an idle session"):
            await self._seed("sess-pause", _stale())
            client = self._client()

        with autotest.step("Act: run one reclaim pass"):
            with patch("worker.idle_reclaim.persist_volatile_configs", AsyncMock(return_value=2)):
                await _reclaim_idle_sessions(client)

        with autotest.step("Assert: paused_at is set and the status is still active"):
            assert_true(await self._paused_at("sess-pause") is not None, "paused_at set")
            async with self.session_factory() as db:
                row = await db.get(LearningSession, "sess-pause")
            assert_equal(row.status, "active", "status unchanged")

    @autotest.num("3405")
    @autotest.external_id("c67914da-6558-4123-a8ba-7068031108fc")
    @autotest.name("reclaim: an already paused session is not reclaimed twice")
    async def test_c67914da_paused_is_skipped(self):
        with autotest.step("Arrange: an idle session that is already paused"):
            await self._seed("sess-done", _stale(), paused_at=datetime.now(UTC))
            client = self._client()

        with autotest.step("Act: run one reclaim pass"):
            with patch("worker.idle_reclaim.persist_volatile_configs", AsyncMock(return_value=0)):
                await _reclaim_idle_sessions(client)

        with autotest.step("Assert: nothing was stopped"):
            assert_equal(client.bulk_node_action.await_count, 0, "no stop")

    @autotest.num("3406")
    @autotest.external_id("db030435-6e11-41f4-8baf-32945b016cdb")
    @autotest.name("reclaim: recent gns3 topology activity spares a stale session")
    async def test_db030435_gns3_activity_spares(self):
        with autotest.step("Arrange: a stale stamp but a fresh gns3 event"):
            await self._seed("sess-topo", _stale())
            client = self._client(activity_ts=_fresh().isoformat())

        with autotest.step("Act: run one reclaim pass"):
            with patch("worker.idle_reclaim.persist_volatile_configs", AsyncMock(return_value=0)):
                await _reclaim_idle_sessions(client)

        with autotest.step("Assert: the session was spared"):
            assert_equal(client.bulk_node_action.await_count, 0, "no stop")
            assert_true(await self._paused_at("sess-topo") is None, "not paused")


class TestPersistTargets:
    """Only started VPCS nodes hold volatile config."""

    @autotest.num("3407")
    @autotest.external_id("75a10eab-f336-42b5-b615-522997090953")
    @autotest.name("persist targets: switches and stopped nodes are excluded")
    def test_75a10eab_only_started_vpcs(self):
        with autotest.step("Arrange: a topology with a switch and two VPCS, one stopped"):
            data = Gns3NodeStateData().with_stopped("PC2")

        with autotest.step("Act: read the save targets"):
            ports = data.vpcs_ports

        with autotest.step("Assert: only the started VPCS node remains"):
            assert_equal(ports, [2011], "one target")

    @autotest.num("3447")
    @autotest.external_id("33299156-cf15-4654-adb5-e0b000b6794c")
    @autotest.name("persist targets: the camelCase payload shape is recognised too")
    def test_33299156_camel_case_shape(self):
        with autotest.step("Arrange: the same topology in the api-layer shape"):
            data = Gns3NodeStateData(camel=True).with_stopped("PC2")

        with autotest.step("Act: read the save targets"):
            ports = data.vpcs_ports

        with autotest.step("Assert: node type is found under either spelling"):
            assert_equal(ports, [2011], "one target")
