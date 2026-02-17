import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab, LabStep
from models.user import User
from tests.report import autotests

pytestmark = pytest.mark.progress

MOCK_USER_ID = "test-user-id-001"


class TestGetAllProgress:
    @autotests.num("130")
    @autotests.external_id("progress-router-get-all-empty")
    @autotests.name("GET /users/me/progress: пустой прогресс")
    async def test_empty(self, auth_client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём пользователя"):
            db_session.add(
                User(id=MOCK_USER_ID, name="Test", email="mock-progress@test.com")
            )
            await db_session.commit()

        with autotests.step("Запрашиваем прогресс"):
            resp = await auth_client.get("/users/me/progress")

        with autotests.step("Проверяем пустой прогресс"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["courses"] == []
            assert data["labs"] == []

    @autotests.num("131")
    @autotests.external_id("progress-router-get-all-unauth")
    @autotests.name("GET /users/me/progress: без авторизации")
    async def test_unauth(self, client: AsyncClient):
        with autotests.step("Запрашиваем без токена"):
            resp = await client.get("/users/me/progress")

        with autotests.step("Проверяем HTTP 401"):
            assert resp.status_code == 401


class TestStartLab:
    @autotests.num("132")
    @autotests.external_id("progress-router-start-lab")
    @autotests.name("POST /users/me/progress/labs/{slug}/start: начало лабы")
    async def test_start(self, auth_client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём пользователя и лабу"):
            db_session.add(
                User(id=MOCK_USER_ID, name="Test", email="mock-start@test.com")
            )
            await db_session.commit()
            db_session.add(
                Lab(
                    slug="start-lab",
                    title="Start",
                    difficulty="beginner",
                    environment_type="docker",
                    order_in_course=0,
                )
            )
            await db_session.commit()

        with autotests.step("Начинаем лабу"):
            resp = await auth_client.post("/users/me/progress/labs/start-lab/start")

        with autotests.step("Проверяем ответ"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["lab_slug"] == "start-lab"
            assert data["status"] == "in_progress"


class TestRecordAttempt:
    @autotests.num("133")
    @autotests.external_id("progress-router-record-attempt")
    @autotests.name(
        "POST /users/me/progress/labs/{slug}/steps/{step}/attempt: запись попытки"
    )
    async def test_record(self, auth_client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём пользователя, лабу и степ"):
            db_session.add(
                User(id=MOCK_USER_ID, name="Test", email="mock-attempt@test.com")
            )
            await db_session.commit()
            db_session.add(
                Lab(
                    slug="attempt-lab",
                    title="Attempt",
                    difficulty="beginner",
                    environment_type="docker",
                    order_in_course=0,
                )
            )
            await db_session.commit()
            db_session.add(
                LabStep(
                    lab_slug="attempt-lab",
                    slug="s1",
                    title="Step 1",
                    step_order=1,
                    validation_type="command",
                )
            )
            await db_session.commit()

        with autotests.step("Записываем попытку"):
            resp = await auth_client.post(
                "/users/me/progress/labs/attempt-lab/steps/s1/attempt",
                json={"result": "pass", "score": 95.0},
            )

        with autotests.step("Проверяем ответ"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["step_slug"] == "s1"
            assert data["attempt_number"] == 1
            assert data["result"] == "pass"
