import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab
from models.user import User
from sessions.service import create_session, end_session, get_user_sessions
from tests.report import autotests

pytestmark = pytest.mark.sessions


class TestCreateSession:
    @autotests.num("140")
    @autotests.external_id("sessions-service-create")
    @autotests.name("create_session: создание сессии")
    async def test_creates(
        self, db_session: AsyncSession, session_user: User, session_lab: Lab
    ):
        with autotests.step("Создаём сессию"):
            s = await create_session(db_session, session_user.id, session_lab.slug)

        with autotests.step("Проверяем сессию"):
            assert s.user_id == session_user.id
            assert s.lab_slug == session_lab.slug
            assert s.status == "active"
            assert s.started_at is not None


class TestEndSession:
    @autotests.num("141")
    @autotests.external_id("sessions-service-end")
    @autotests.name("end_session: завершение сессии")
    async def test_ends(
        self, db_session: AsyncSession, session_user: User, session_lab: Lab
    ):
        with autotests.step("Создаём и завершаем сессию"):
            s = await create_session(db_session, session_user.id, session_lab.slug)
            ended = await end_session(db_session, s.id, session_user.id, "completed")

        with autotests.step("Проверяем завершённую сессию"):
            assert ended is not None
            assert ended.status == "completed"
            assert ended.ended_at is not None

    @autotests.num("142")
    @autotests.external_id("sessions-service-end-not-found")
    @autotests.name("end_session: не найдена")
    async def test_not_found(self, db_session: AsyncSession, session_user: User):
        with autotests.step("Завершаем несуществующую сессию"):
            result = await end_session(
                db_session, "nonexistent-id", session_user.id, "completed"
            )

        with autotests.step("Проверяем None"):
            assert result is None


class TestGetUserSessions:
    @autotests.num("143")
    @autotests.external_id("sessions-service-get-user")
    @autotests.name("get_user_sessions: список сессий пользователя")
    async def test_returns_sessions(
        self, db_session: AsyncSession, session_user: User, session_lab: Lab
    ):
        with autotests.step("Создаём две сессии"):
            await create_session(db_session, session_user.id, session_lab.slug)
            await create_session(db_session, session_user.id, session_lab.slug)

        with autotests.step("Запрашиваем сессии"):
            sessions = await get_user_sessions(db_session, session_user.id)

        with autotests.step("Проверяем количество"):
            assert len(sessions) >= 2
