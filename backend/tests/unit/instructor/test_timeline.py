"""Unit-тесты для build_session_timeline и эндпоинта /timeline."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from instructor.service import build_session_timeline
from models.behavioral_event import BehavioralEvent
from models.chat_message import ChatMessage
from models.lab import Lab
from models.progress import LabProgress, StepAttempt
from models.session import LearningSession
from models.user import User

pytestmark = [pytest.mark.unit]


def _ts(offset_seconds: int = 0) -> datetime:
    """Опорное время с заданным смещением в секундах."""
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds)


class TestBuildSessionTimeline:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
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

    async def _seed_timeline(self):
        """Сессия с user-msg (t0), intervention (t1), assistant-msg (t2)."""
        async with self.session_factory() as db:
            db.add_all(
                [
                    User(id="stud-t", name="Таймлайн", email="tl@test.local", role="student"),
                    Lab(slug="tl-lab", title="TL Lab"),
                    LearningSession(
                        id="sess-tl",
                        user_id="stud-t",
                        lab_slug="tl-lab",
                        status="in_progress",
                        started_at=_ts(0),
                    ),
                    # t=0: вопрос студента
                    ChatMessage(
                        id="msg-tl-1",
                        session_id="sess-tl",
                        role="user",
                        parts=[{"type": "text", "text": "Вопрос"}],
                        created_at=_ts(0),
                    ),
                    # t=2: ассистент отвечает
                    ChatMessage(
                        id="msg-tl-2",
                        session_id="sess-tl",
                        role="assistant",
                        parts=[{"type": "text", "text": "Ответ"}],
                        created_at=_ts(2),
                    ),
                    # t=1: интервенция между ними
                    BehavioralEvent(
                        id="evt-tl-1",
                        session_id="sess-tl",
                        user_id="stud-t",
                        lab_slug="tl-lab",
                        timestamp=_ts(1),
                        event_type="intervention",
                        action="intervene_hint",
                        success=True,
                        message="Подсказка",
                        extra_data={"hint_level": 2, "struggle_type": "config_error"},
                    ),
                ]
            )
            await db.commit()

    @autotest.num("1880")
    @autotest.external_id("c1a2b3d4-e5f6-4708-8901-aabbccdd0020")
    @autotest.name("build_session_timeline: student → intervention → tutor по времени")
    async def test_timeline_merges_in_time_order(self):
        with autotest.step("Arrange: сеем сессию с msg-evt-msg"):
            await self._seed_timeline()

        with autotest.step("Act"):
            async with self.session_factory() as db:
                items = await build_session_timeline(db, "sess-tl")

        with autotest.step("Assert: порядок kind и поля интервенции"):
            assert_equal(
                [i["kind"] for i in items], ["student", "intervention", "tutor"], "порядок"
            )
            assert_equal(items[1]["hint_level"], 2, "hint_level из extra_data")
            assert_equal(items[1]["struggle_type"], "config_error", "struggle_type")
            assert_equal(items[1]["text"], "Подсказка", "text интервенции")
            assert_equal(items[0]["parts"], [{"type": "text", "text": "Вопрос"}], "parts студента")

    @autotest.num("1881")
    @autotest.external_id("c1a2b3d4-e5f6-4708-8901-aabbccdd0021")
    @autotest.name("build_session_timeline: пустая сессия → []")
    async def test_timeline_empty_session(self):
        with autotest.step("Act: несуществующая сессия"):
            async with self.session_factory() as db:
                items = await build_session_timeline(db, "no-such-session")

        with autotest.step("Assert: пустой список"):
            assert_equal(items, [], "пустой таймлайн")

    @autotest.num("1882")
    @autotest.external_id("c1a2b3d4-e5f6-4708-8901-aabbccdd0022")
    @autotest.name("build_session_timeline: не-intervention события игнорируются")
    async def test_timeline_ignores_non_intervention_events(self):
        with autotest.step("Arrange: сессия с command-событием"):
            async with self.session_factory() as db:
                db.add_all(
                    [
                        User(id="stud-cmd", name="CMD", email="cmd@test.local", role="student"),
                        Lab(slug="cmd-lab", title="CMD Lab"),
                        LearningSession(
                            id="sess-cmd",
                            user_id="stud-cmd",
                            lab_slug="cmd-lab",
                            status="active",
                            started_at=_ts(0),
                        ),
                        BehavioralEvent(
                            id="evt-cmd-1",
                            session_id="sess-cmd",
                            user_id="stud-cmd",
                            lab_slug="cmd-lab",
                            timestamp=_ts(0),
                            event_type="command",
                            action="ping",
                            success=True,
                        ),
                    ]
                )
                await db.commit()

        with autotest.step("Act"):
            async with self.session_factory() as db:
                items = await build_session_timeline(db, "sess-cmd")

        with autotest.step("Assert: command-событие не попало"):
            assert_equal(items, [], "command не включается в таймлайн")

    @autotest.num("1883")
    @autotest.external_id("c1a2b3d4-e5f6-4708-8901-aabbccdd0023")
    @autotest.name("student_session_timeline endpoint: чужая сессия → 404")
    async def test_endpoint_foreign_session_returns_404(self):
        with autotest.step("Arrange: сессия принадлежит другому пользователю"):
            async with self.session_factory() as db:
                db.add_all(
                    [
                        User(id="owner", name="Owner", email="owner@test.local", role="student"),
                        Lab(slug="ep-lab", title="EP Lab"),
                        LearningSession(
                            id="sess-ep",
                            user_id="owner",
                            lab_slug="ep-lab",
                            status="active",
                            started_at=_ts(0),
                        ),
                    ]
                )
                await db.commit()

        with autotest.step("Act + Assert: user_id='other' → 404"):
            from instructor.router import student_session_timeline

            async with self.session_factory() as db:
                with pytest.raises(HTTPException) as exc_info:
                    await student_session_timeline(
                        user_id="other",
                        session_id="sess-ep",
                        _={"id": "instr", "role": "instructor"},
                        db=db,
                    )
            assert_equal(exc_info.value.status_code, 404, "status 404")
            assert_equal(exc_info.value.detail, "Session not found", "detail")

    @autotest.num("1884")
    @autotest.external_id("c1a2b3d4-e5f6-4708-8901-aabbccdd0024")
    @autotest.name("student_session_timeline endpoint: несуществующая сессия → 404")
    async def test_endpoint_missing_session_returns_404(self):
        with autotest.step("Act + Assert: session_id не существует → 404"):
            from instructor.router import student_session_timeline

            async with self.session_factory() as db:
                with pytest.raises(HTTPException) as exc_info:
                    await student_session_timeline(
                        user_id="any-user",
                        session_id="ghost-session",
                        _={"id": "instr", "role": "instructor"},
                        db=db,
                    )
            assert_equal(exc_info.value.status_code, 404, "status 404")
