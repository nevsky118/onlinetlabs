from datetime import UTC, datetime

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in, assert_is_none
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from instructor.service import get_student_detail, get_students_overview
from models.catalog import Lab
from models.identity import User
from models.learning import ChatMessage, LabProgress, LearningSession, StepAttempt
from models.research import BehavioralEvent

pytestmark = [pytest.mark.unit]


def _now() -> datetime:
    return datetime.now(UTC)


class TestInstructorService:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        # Only the needed tables: full metadata contains a JSONB server_default,
        # which SQLite doesn't understand.
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LabProgress.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)
            await conn.run_sync(BehavioralEvent.__table__.create)
            await conn.run_sync(StepAttempt.__table__.create)
            await conn.run_sync(ChatMessage.__table__.create)
        yield
        await self.engine.dispose()

    async def _seed_with_chat(self):
        """Student with 1 session, 2 messages, and 1 intervention."""
        async with self.session_factory() as db:
            db.add_all(
                [
                    User(id="stud-c", name="Чат", email="chat@test.local", role="student"),
                    Lab(slug="chat-lab", title_i18n={"en": "Chat Lab"}),
                    LearningSession(
                        id="sess-c",
                        user_id="stud-c",
                        lab_slug="chat-lab",
                        status="in_progress",
                        started_at=_now(),
                    ),
                    ChatMessage(
                        id="msg-1",
                        session_id="sess-c",
                        role="user",
                        parts=[{"type": "text", "text": "вопрос"}],
                    ),
                    ChatMessage(
                        id="msg-2",
                        session_id="sess-c",
                        role="assistant",
                        parts=[{"type": "text", "text": "ответ"}],
                    ),
                    BehavioralEvent(
                        session_id="sess-c",
                        user_id="stud-c",
                        lab_slug="chat-lab",
                        timestamp=_now(),
                        event_type="intervention",
                        action="intervene_hint",
                        success=True,
                    ),
                ]
            )
            await db.commit()

    async def _seed(self):
        async with self.session_factory() as db:
            db.add_all(
                [
                    User(id="stud-1", name="Иван", email="ivan@test.local", role="student"),
                    User(id="stud-2", name="Пётр", email="petr@test.local", role="student"),
                    User(id="teacher", name="Препод", email="t@test.local", role="instructor"),
                    Lab(slug="dhcp-basics", title_i18n={"en": "DHCP Basics"}),
                    LabProgress(
                        user_id="stud-1",
                        lab_slug="dhcp-basics",
                        status="completed",
                        score=90.0,
                        started_at=_now(),
                        completed_at=_now(),
                    ),
                    LearningSession(
                        id="sess-1",
                        user_id="stud-1",
                        lab_slug="dhcp-basics",
                        status="completed",
                        started_at=_now(),
                    ),
                    # Two hints and one irrelevant event for stud-1
                    BehavioralEvent(
                        session_id="sess-1",
                        user_id="stud-1",
                        lab_slug="dhcp-basics",
                        timestamp=_now(),
                        event_type="intervention",
                        action="intervene_hint",
                        success=True,
                    ),
                    BehavioralEvent(
                        session_id="sess-1",
                        user_id="stud-1",
                        lab_slug="dhcp-basics",
                        timestamp=_now(),
                        event_type="intervention",
                        action="intervene_hint",
                        success=True,
                    ),
                    BehavioralEvent(
                        session_id="sess-1",
                        user_id="stud-1",
                        lab_slug="dhcp-basics",
                        timestamp=_now(),
                        event_type="command",
                        action="ping",
                        success=True,
                    ),
                    StepAttempt(
                        user_id="stud-1",
                        lab_slug="dhcp-basics",
                        step_slug="step-1",
                        attempt_number=1,
                        result="pass",
                    ),
                ]
            )
            await db.commit()

    @autotest.num("743")
    @autotest.external_id("6f531b65-31f8-4783-bff5-ceec98b773b6")
    @autotest.name("get_students_overview: students only, hints = intervention")
    async def test_6f531b65_overview_counts_hints_and_excludes_non_students(self):
        with autotest.step("Arrange: seed students, instructor, and events"):
            await self._seed()

        with autotest.step("Act: fetch overview"):
            async with self.session_factory() as db:
                result = await get_students_overview(db)

        with autotest.step("Assert: 2 students, instructor excluded, hints=2"):
            assert_equal(result["total_students"], 2, "students only")
            assert_equal(result["total_hints"], 2, "total hints")
            by_id = {student["user_id"]: student for student in result["students"]}
            assert_equal(by_id["stud-1"]["total_hints"], 2, "stud-1 hints")
            assert_equal(by_id["stud-1"]["labs_completed"], 1, "completed labs")
            assert_equal(by_id["stud-1"]["avg_score"], 90.0, "average score")
            assert_equal(by_id["stud-2"]["total_hints"], 0, "stud-2 has no hints")

    @autotest.num("744")
    @autotest.external_id("d62eb287-869b-4d68-b2c8-5827e4927f92")
    @autotest.name("get_student_detail: breakdown by lab with title and hints")
    async def test_d62eb287_detail_breaks_down_by_lab(self):
        with autotest.step("Arrange: seed data"):
            await self._seed()

        with autotest.step("Act: fetch stud-1 detail"):
            async with self.session_factory() as db:
                detail = await get_student_detail(db, "stud-1")

        with autotest.step("Assert: lab with title, hints, and attempts"):
            assert_equal(detail["total_hints"], 2, "total hints")
            assert_equal(len(detail["labs"]), 1, "one lab")
            lab = detail["labs"][0]
            assert_equal(lab["lab_title"], "DHCP Basics", "lab title")
            assert_equal(lab["hints"], 2, "hints for lab")
            assert_equal(lab["sessions"], 1, "sessions for lab")
            assert_equal(lab["attempts"], 1, "attempts for lab")

    @autotest.num("745")
    @autotest.external_id("fc258598-ea8f-4e9c-8310-cf5d9740cae7")
    @autotest.name("get_student_detail: unknown student → None")
    async def test_fc258598_detail_unknown_user_returns_none(self):
        with autotest.step("Act: request nonexistent student"):
            async with self.session_factory() as db:
                detail = await get_student_detail(db, "ghost")

        with autotest.step("Assert: None"):
            assert_is_none(detail, "detail is None")

    @autotest.num("746")
    @autotest.external_id("f148d464-0220-428f-b136-a2dbce7639b3")
    @autotest.name("get_student_detail: sessions with message_count and hint_count")
    async def test_f148d464_detail_sessions_message_and_hint_counts(self):
        with autotest.step("Arrange: student with one session, 2 messages, 1 intervention"):
            await self._seed_with_chat()

        with autotest.step("Act"):
            async with self.session_factory() as db:
                detail = await get_student_detail(db, "stud-c")

        with autotest.step("Assert"):
            assert_in("sessions", detail, "sessions is present in the detail")
            assert_equal(len(detail["sessions"]), 1, "one session")
            detail_2 = detail["sessions"][0]
            assert_equal(detail_2["message_count"], 2, "two messages")
            assert_equal(detail_2["hint_count"], 1, "one hint")
