import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab
from models.user import User
from tests.report import autotests

pytestmark = pytest.mark.sessions

MOCK_USER_ID = "test-user-id-001"


class TestListSessions:
    @autotests.num("144")
    @autotests.external_id("sessions-router-list-empty")
    @autotests.name("GET /users/me/sessions: пустой список")
    async def test_empty(self, auth_client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём пользователя"):
            db_session.add(
                User(id=MOCK_USER_ID, name="Test", email="mock-sess@test.com")
            )
            await db_session.commit()

        with autotests.step("Запрашиваем сессии"):
            resp = await auth_client.get("/users/me/sessions")

        with autotests.step("Проверяем пустой массив"):
            assert resp.status_code == 200
            assert resp.json() == []

    @autotests.num("145")
    @autotests.external_id("sessions-router-list-unauth")
    @autotests.name("GET /users/me/sessions: без авторизации")
    async def test_unauth(self, client: AsyncClient):
        with autotests.step("Запрашиваем без токена"):
            resp = await client.get("/users/me/sessions")

        with autotests.step("Проверяем HTTP 401"):
            assert resp.status_code == 401


class TestCreateSession:
    @autotests.num("146")
    @autotests.external_id("sessions-router-create")
    @autotests.name("POST /users/me/sessions: создание сессии")
    async def test_create(self, auth_client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём пользователя и лабу"):
            db_session.add(
                User(id=MOCK_USER_ID, name="Test", email="mock-create-sess@test.com")
            )
            await db_session.commit()
            db_session.add(
                Lab(
                    slug="sess-lab",
                    title="Sess Lab",
                    difficulty="beginner",
                    environment_type="docker",
                    order_in_course=0,
                )
            )
            await db_session.commit()

        with autotests.step("Создаём сессию"):
            resp = await auth_client.post(
                "/users/me/sessions", json={"lab_slug": "sess-lab"}
            )

        with autotests.step("Проверяем ответ"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["lab_slug"] == "sess-lab"
            assert data["status"] == "active"


class TestUpdateSession:
    @autotests.num("147")
    @autotests.external_id("sessions-router-update")
    @autotests.name("PATCH /users/me/sessions/{id}: завершение сессии")
    async def test_update(self, auth_client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём пользователя, лабу и сессию"):
            db_session.add(
                User(id=MOCK_USER_ID, name="Test", email="mock-update-sess@test.com")
            )
            await db_session.commit()
            db_session.add(
                Lab(
                    slug="upd-lab",
                    title="Update Lab",
                    difficulty="beginner",
                    environment_type="docker",
                    order_in_course=0,
                )
            )
            await db_session.commit()
            create_resp = await auth_client.post(
                "/users/me/sessions", json={"lab_slug": "upd-lab"}
            )
            session_id = create_resp.json()["id"]

        with autotests.step("Завершаем сессию"):
            resp = await auth_client.patch(
                f"/users/me/sessions/{session_id}", json={"status": "completed"}
            )

        with autotests.step("Проверяем ответ"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "completed"
            assert data["ended_at"] is not None
