"""Subject access: pseudonyms in exports, and that erasure reaches every registry table."""

import json
from datetime import UTC, datetime

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from admin.data_registry import ADMIN_TABLES
from models.base import Base
from models.behavioral_event import BehavioralEvent
from models.consent import Consent
from models.lab import Lab
from models.mcp_audit import MCPAudit
from models.regime_annotation import RegimeAnnotation
from models.session import LearningSession
from models.study_participant import StudyParticipant
from models.user import User
from research.pseudonyms import pseudonym_for
from users.data_export import (
    collect_subject_data,
    erase_subject,
    subject_filter,
    unattributable_tables,
)

pytestmark = [pytest.mark.unit]

_SUBJECT = "user-subject-1"
_OTHER = "user-subject-2"
_SESSION = "sess-subject-1"
_NOW = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)


class TestRegistryCoverage:
    """A table nobody can attribute is a table erasure would silently skip."""

    @autotest.num("3417")
    @autotest.external_id("f5483d69-8a85-47c1-bea4-def385c61dc7")
    @autotest.name("registry: every table is reachable by user_id or session_id")
    def test_f5483d69_every_table_is_attributable(self):
        with autotest.step("Act: look for tables neither key can reach"):
            orphans = unattributable_tables()

        with autotest.step("Assert: none"):
            assert_equal(orphans, [], "all tables attributable")

    @autotest.num("3418")
    @autotest.external_id("dfce050c-2161-46f2-bbcd-e880f2d2f252")
    @autotest.name("registry: the tables the earlier audit found missing are present")
    def test_dfce050c_previously_missing_tables_registered(self):
        with autotest.step("Arrange: the six tables the sweep found absent"):
            expected = {
                "intervention_decisions",
                "session_evidence_snapshots",
                "regime_annotations",
                "grounding_comparisons",
                "cycle_latency_samples",
                "study_participants",
            }

        with autotest.step("Act + Assert: all are registered"):
            missing = expected - set(ADMIN_TABLES)
            assert_equal(missing, set(), "no table left out")

    @autotest.num("3419")
    @autotest.external_id("5e3e94fb-5eb2-4e46-a2a8-b260d5b5fac1")
    @autotest.name("subject_filter: a session-keyed table with no sessions matches nothing")
    def test_5e3e94fb_session_keyed_without_sessions(self):
        with autotest.step("Act: build a filter for a learner with no sessions"):
            condition = subject_filter(RegimeAnnotation, _SUBJECT, [])

        with autotest.step("Assert: None, rather than a filter that matches every row"):
            assert_true(condition is None, "no blanket match")


class TestSubjectData:
    """Export and erasure across a user-keyed and a session-keyed table."""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await self._seed()
        yield
        await self.engine.dispose()

    async def _seed(self) -> None:
        """One learner with a session, a behavioural row, an audit row and an annotation."""
        async with self.session_factory() as db:
            db.add(Lab(slug="lab-x", title_i18n={"en": "Lab"}))
            db.add(User(id=_SUBJECT, email="subject@test.local"))
            db.add(User(id=_OTHER, email="other@test.local"))
            db.add(StudyParticipant(user_id=_SUBJECT))
            db.add(
                LearningSession(id=_SESSION, user_id=_SUBJECT, lab_slug="lab-x", started_at=_NOW)
            )
            db.add(
                BehavioralEvent(
                    id="be-1",
                    session_id=_SESSION,
                    user_id=_SUBJECT,
                    lab_slug="lab-x",
                    timestamp=_NOW,
                    event_type="action",
                    action="check_passed",
                    success=True,
                )
            )
            db.add(
                MCPAudit(
                    id="au-1",
                    user_id=_SUBJECT,
                    session_id=_SESSION,
                    tool="list_user_actions",
                    kind="observe",
                    success=True,
                )
            )
            db.add(
                RegimeAnnotation(
                    id="ra-1",
                    session_id=_SESSION,
                    coder_id="gold",
                    window_index=0,
                    regime_label="idle",
                    is_gold=True,
                )
            )
            db.add(
                Consent(
                    id="c-1",
                    user_id=_SUBJECT,
                    scope="study",
                    observe=True,
                    act=True,
                    decision="granted",
                    policy_version="1",
                )
            )
            await db.commit()

    @autotest.num("3420")
    @autotest.external_id("7298714d-3b9c-47e7-b385-57040a81ca92")
    @autotest.name("export: reaches both user-keyed and session-keyed tables")
    async def test_7298714d_export_covers_both_keys(self):
        with autotest.step("Act: export everything held about the learner"):
            async with self.session_factory() as db:
                data = await collect_subject_data(db, _SUBJECT)

        with autotest.step("Assert: rows from a user-keyed and a session-keyed table"):
            assert_equal(len(data["behavioral_events"]), 1, "user-keyed row")
            assert_equal(len(data["regime_annotations"]), 1, "session-keyed row")
            assert_equal(len(data["learning_sessions"]), 1, "session row")
            assert_equal(len(data["consents"]), 1, "consent row")

    @autotest.num("3421")
    @autotest.external_id("c3726e2d-1c3a-4513-b00b-b210ce3a1e7c")
    @autotest.name("export: another learner's rows never appear")
    async def test_c3726e2d_export_is_scoped(self):
        with autotest.step("Act: export for the learner who owns nothing"):
            async with self.session_factory() as db:
                data = await collect_subject_data(db, _OTHER)

        with autotest.step("Assert: every table is empty"):
            total = sum(len(rows) for rows in data.values())
            assert_equal(total, 0, "no rows leaked")

    @autotest.num("3422")
    @autotest.external_id("a7ce5a92-39f1-4f8e-886e-2fda3c97f8a7")
    @autotest.name("erasure: every registry table is emptied, the other learner untouched")
    async def test_a7ce5a92_erasure_is_complete(self):
        with autotest.step("Act: erase the learner"):
            async with self.session_factory() as db:
                await erase_subject(db, _SUBJECT)

        with autotest.step("Assert: nothing of theirs remains, in any table"):
            async with self.session_factory() as db:
                remaining = await collect_subject_data(db, _SUBJECT)
                total = sum(len(rows) for rows in remaining.values())
                other = (
                    await db.execute(select(User).where(User.id == _OTHER))
                ).scalar_one_or_none()
            assert_equal(total, 0, "subject erased")
            assert_true(other is not None, "other learner untouched")

    @autotest.num("3423")
    @autotest.external_id("0d6aafc4-06ac-4817-ba05-1a784dcbea0c")
    @autotest.name("erasure: the account itself is removed")
    async def test_0d6aafc4_account_removed(self):
        with autotest.step("Act: erase the learner"):
            async with self.session_factory() as db:
                removed = await erase_subject(db, _SUBJECT)

        with autotest.step("Assert: the user row is gone"):
            assert_equal(removed["users"], 1, "account deleted")
            async with self.session_factory() as db:
                found = (
                    await db.execute(select(User).where(User.id == _SUBJECT))
                ).scalar_one_or_none()
            assert_true(found is None, "no user row")

    @autotest.num("3424")
    @autotest.external_id("a36b61cd-d1a3-4cbe-a51b-1a8c704ddaf5")
    @autotest.name("pseudonym: stable per learner, and not derived from the account id")
    async def test_a36b61cd_pseudonym_is_stable_and_opaque(self):
        with autotest.step("Act: resolve the pseudonym twice"):
            async with self.session_factory() as db:
                first = await pseudonym_for(db, _SUBJECT)
                second = await pseudonym_for(db, _SUBJECT)

        with autotest.step("Assert: same value, and it contains no part of the account id"):
            assert_equal(first, second, "stable")
            assert_true(_SUBJECT not in first, "not derived from user id")
            assert_true(len(first) == 36, "uuid shaped")

    @autotest.num("3425")
    @autotest.external_id("5e3e94fb-5eb2-4e46-a2a8-b260d5b5fac2")
    @autotest.name("research export: carries no address, name or raw identifier")
    async def test_5e3e94fb_export_carries_no_identity(self):
        with autotest.step("Arrange: an intervention decision for the seeded learner"):
            from evaluation.reproducibility import build_reproducibility_bundle
            from models.intervention_decision import InterventionDecision

            async with self.session_factory() as db:
                db.add(
                    InterventionDecision(
                        id="d-1",
                        session_id=_SESSION,
                        user_id=_SUBJECT,
                        lab_slug="lab-x",
                        spell_id="sp-1",
                        ts=_NOW,
                        regime="idle",
                        dwell_seconds=10.0,
                        t_k_applied=0.0,
                        assignment="intervene",
                    )
                )
                await db.commit()

        with autotest.step("Act: build the research bundle"):
            async with self.session_factory() as db:
                bundle = await build_reproducibility_bundle(db)

        with autotest.step("Assert: no email, no account id, no raw session id"):
            blob = json.dumps(bundle)
            assert_true("subject@test.local" not in blob, "no email")
            assert_true(_SUBJECT not in blob, "no account id")
            assert_true(_SESSION not in blob, "no raw session id")
            assert_true(bundle["intervention_decisions"][0]["user"] is not None, "has pseudonym")
