"""Consent as a gate: asked before launch, honoured on the write path, never gating the lab."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from control_interface.consent import (
    CURRENT_POLICY_VERSION,
    DECLINED,
    GRANTED,
    STUDY_SCOPE,
    has_consent,
    may_collect,
    record,
    study_decision,
)
from control_interface.registry import ToolKind
from i18n import LocalizedError
from models.consent import Consent
from rate_limit import limiter
from sessions.routers import commands as launch_mod

pytestmark = [pytest.mark.unit]

_LEARNER = "user-consent-1"
_CREDS = {
    "gns3_username": "student",
    "gns3_password": "pw",
    "gns3_url": "http://gns3/x",
    "gns3_deep_url": "http://gns3/x/deep",
}


class TestStudyDecision:
    """A refusal is a recorded answer, distinct from never having been asked."""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Consent.__table__.create)
        yield
        await self.engine.dispose()

    @autotest.num("3408")
    @autotest.external_id("1aa4cc79-6e5d-4715-ac0d-9d3233bca78a")
    @autotest.name("study_decision: never asked returns None")
    async def test_1aa4cc79_never_asked_is_none(self):
        with autotest.step("Act: read the decision for a learner with no rows"):
            async with self.session_factory() as db:
                decision = await study_decision(db, _LEARNER)

        with autotest.step("Assert: None, which is what the launch gate blocks on"):
            assert_true(decision is None, "no decision on file")

    @autotest.num("3409")
    @autotest.external_id("60bcc3fb-09fe-4c57-afcd-3db3b04c9649")
    @autotest.name("study_decision: a refusal is stored and read back")
    async def test_60bcc3fb_decline_is_recorded(self):
        with autotest.step("Arrange: the learner declines"):
            async with self.session_factory() as db:
                await record(db, _LEARNER, STUDY_SCOPE, False, False, decision=DECLINED)

        with autotest.step("Act: read the decision back"):
            async with self.session_factory() as db:
                decision = await study_decision(db, _LEARNER)

        with autotest.step("Assert: declined, not absent"):
            assert_equal(decision, DECLINED, "refusal persisted")

    @autotest.num("3410")
    @autotest.external_id("0c24d99b-b305-4ffa-bb31-73853a6d4762")
    @autotest.name("may_collect: only an explicit grant permits collection")
    async def test_0c24d99b_may_collect_requires_grant(self):
        with autotest.step("Arrange: one learner declines, another grants"):
            async with self.session_factory() as db:
                await record(db, "decliner", STUDY_SCOPE, False, False, decision=DECLINED)
                await record(db, "granter", STUDY_SCOPE, True, True, decision=GRANTED)

        with autotest.step("Act: ask about all three states"):
            async with self.session_factory() as db:
                silent = await may_collect(db, "never-asked")
                declined = await may_collect(db, "decliner")
                granted = await may_collect(db, "granter")

        with autotest.step("Assert: silence and refusal both mean no"):
            assert_equal(silent, False, "never asked")
            assert_equal(declined, False, "declined")
            assert_equal(granted, True, "granted")

    @autotest.num("3411")
    @autotest.external_id("be0c1de1-b50b-4c00-813a-03e025986a34")
    @autotest.name("has_consent: a declined study row does not authorize observe")
    async def test_be0c1de1_declined_study_row_denies(self):
        with autotest.step("Arrange: a declined study consent"):
            async with self.session_factory() as db:
                await record(db, _LEARNER, STUDY_SCOPE, False, False, decision=DECLINED)

        with autotest.step("Act: ask whether observe is permitted"):
            async with self.session_factory() as db:
                allowed = await has_consent(db, _LEARNER, ToolKind.OBSERVE)

        with autotest.step("Assert: denied, the study scope no longer short-circuits"):
            assert_equal(allowed, False, "observe denied")

    @autotest.num("3412")
    @autotest.external_id("cf7f4691-7760-47ae-8fff-4be87ca73300")
    @autotest.name("study_decision: an answer to older wording does not count")
    async def test_cf7f4691_stale_policy_version_is_ignored(self):
        with autotest.step("Arrange: a grant recorded against the previous wording"):
            async with self.session_factory() as db:
                await record(
                    db,
                    _LEARNER,
                    STUDY_SCOPE,
                    True,
                    True,
                    decision=GRANTED,
                    policy_version="0",
                )

        with autotest.step("Act: read the decision for the current wording"):
            async with self.session_factory() as db:
                decision = await study_decision(db, _LEARNER)

        with autotest.step("Assert: the gate re-asks"):
            assert_true(decision is None, "stale version ignored")
            assert_equal(CURRENT_POLICY_VERSION, "1", "current version")


class TestLaunchConsentGate:
    """Launch is blocked until the question is answered, and allowed once it is."""

    @pytest.fixture(autouse=True)
    def _disable_limiter(self):
        prev = limiter.enabled
        limiter.enabled = False
        yield
        limiter.enabled = prev

    def _mocks(self):
        """A queue and registry that record whether the launch got that far."""
        queue = MagicMock()
        queue.try_acquire = AsyncMock(return_value=True)
        queue.enqueue = AsyncMock(return_value=1)
        queue.queue_depth = AsyncMock(return_value=1)
        queue.release = AsyncMock()
        monitor_registry = MagicMock()
        monitor_registry.start = AsyncMock()
        return queue, monitor_registry

    async def _call(self, queue, monitor_registry):
        """Invokes the launch handler directly."""
        return await launch_mod.launch_endpoint(
            request=SimpleNamespace(),
            body=SimpleNamespace(lab_slug="lab-x"),
            current_user={"id": _LEARNER},
            _active={"id": _LEARNER},
            db=MagicMock(),
            db_factory=MagicMock(),
            gns3_client=MagicMock(),
            monitor_registry=monitor_registry,
            queue=queue,
        )

    @autotest.num("3413")
    @autotest.external_id("5271ddf8-76d6-4caa-93e7-a86ef613d3dc")
    @autotest.name("launch: refused before any session row exists when consent is unanswered")
    async def test_5271ddf8_unanswered_consent_blocks_launch(self):
        with autotest.step("Arrange: a learner who has never been asked"):
            queue, monitor_registry = self._mocks()

        with autotest.step("Act + Assert: the launch raises before touching the queue"):
            raised = False
            with patch.object(launch_mod, "study_decision", AsyncMock(return_value=None)):
                try:
                    await self._call(queue, monitor_registry)
                except LocalizedError as exc:
                    raised = True
                    assert_equal(exc.key, "error.consent.required", "code")
                    assert_equal(exc.status_code, 428, "status 428")
            assert_true(raised, "LocalizedError was raised")
            queue.try_acquire.assert_not_awaited()
            monitor_registry.start.assert_not_awaited()

    @autotest.num("3414")
    @autotest.external_id("46c60b6f-d449-49a7-93f5-13c664352ff2")
    @autotest.name("launch: a learner who declined still gets their lab")
    async def test_46c60b6f_decline_does_not_block_the_lab(self):
        with autotest.step("Arrange: a recorded refusal"):
            queue, monitor_registry = self._mocks()
            session = SimpleNamespace(id="s1", user_id=_LEARNER, lab_slug="lab-x", status="active")

        with autotest.step("Act: launch with decision=declined"):
            with (
                patch.object(launch_mod, "study_decision", AsyncMock(return_value=DECLINED)),
                patch.object(launch_mod, "get_active_session", AsyncMock(return_value=None)),
                patch.object(
                    launch_mod, "launch_session", AsyncMock(return_value=(session, _CREDS))
                ),
                patch.object(launch_mod, "build_session_context", MagicMock(return_value=object())),
                patch("observability.metrics.active_sessions_gauge"),
            ):
                resp = await self._call(queue, monitor_registry)

        with autotest.step("Assert: the session was created normally"):
            assert_equal(resp.status, "active", "launched")
            assert_equal(resp.session_id, "s1", "session id")


class TestObserverHonoursRefusal:
    """The observer writes nothing for a learner who did not agree."""

    def _observer(self):
        """An observer wired to a db factory that must never be used."""
        from learning_analytics.progress_observer import LabProgressObserver

        cfg = SimpleNamespace(progress_max_duration_hours=12, progress_poll_interval=5)
        observer = LabProgressObserver(MagicMock(), MagicMock(), MagicMock(), cfg)
        observer._user_id = _LEARNER
        observer._session_id = "s1"
        observer._lab_slug = "lab-x"
        return observer

    @autotest.num("3415")
    @autotest.external_id("d9ad557b-d2a7-41f7-b0a3-54bb1e0cb465")
    @autotest.name("observer: no behavioural rows are written without consent")
    async def test_d9ad557b_no_write_without_consent(self):
        with autotest.step("Arrange: an observer for a learner who declined"):
            observer = self._observer()

        with autotest.step("Act: persist one event"):
            with patch.object(observer, "_may_collect", AsyncMock(return_value=False)):
                await observer._persist([{"action": "check_passed"}])

        with autotest.step("Assert: the db factory was never opened"):
            assert_equal(observer._db_factory.call_count, 0, "no db session")

    @autotest.num("3416")
    @autotest.external_id("1964b7c0-72a8-4cdb-85a5-01b037739649")
    @autotest.name("observer: consent lookup failure denies rather than collects")
    async def test_1964b7c0_lookup_failure_denies(self):
        with autotest.step("Arrange: a db factory that raises on use"):
            observer = self._observer()
            observer._db_factory = MagicMock(side_effect=RuntimeError("db down"))

        with autotest.step("Act: ask whether collection is permitted"):
            allowed = await observer._may_collect()

        with autotest.step("Assert: denied"):
            assert_equal(allowed, False, "fails closed")
