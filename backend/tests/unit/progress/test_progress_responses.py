"""Characterization: /progress endpoints — exact JSON response."""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.dependencies import get_current_user
from db.session import get_db
from models.progress import CourseProgress, LabProgress, StepAttempt
from models.user import User
from progress.router import router as progress_router

pytestmark = [pytest.mark.unit]

_USER_ID = "u-progress-1"
_STARTED_AT = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_COMPLETED_AT = datetime(2026, 1, 1, 11, 0, 0, tzinfo=UTC)


class TestProgressResponses:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(CourseProgress.__table__.create)
            await conn.run_sync(LabProgress.__table__.create)
            await conn.run_sync(StepAttempt.__table__.create)

        async with self.session_factory() as db:
            db.add(User(id=_USER_ID, email="progress-json@test.local", role="student"))
            db.add(
                CourseProgress(
                    id="cp-1",
                    user_id=_USER_ID,
                    course_slug="networking-101",
                    status="in_progress",
                    score=42.5,
                    started_at=_STARTED_AT,
                    completed_at=None,
                )
            )
            db.add(
                LabProgress(
                    id="lp-1",
                    user_id=_USER_ID,
                    lab_slug="ospf-lab",
                    status="completed",
                    score=100.0,
                    current_step=3,
                    started_at=_STARTED_AT,
                    completed_at=_COMPLETED_AT,
                )
            )
            db.add(
                StepAttempt(
                    id="sa-1",
                    user_id=_USER_ID,
                    lab_slug="ospf-lab",
                    step_slug="step-1",
                    attempt_number=1,
                    result="pass",
                    score=100.0,
                    started_at=_STARTED_AT,
                    ended_at=_COMPLETED_AT,
                )
            )
            await db.commit()

        self.app = FastAPI()
        self.app.include_router(progress_router, prefix="/progress")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        self.app.dependency_overrides[get_db] = _override_db
        self.app.dependency_overrides[get_current_user] = lambda: {
            "id": _USER_ID,
            "role": "student",
        }
        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    @autotest.num("2505")
    @autotest.external_id("0155438f-4bde-4e28-9aa5-57921a6a4779")
    @autotest.name("GET /progress: полный JSON прогресса по курсам и лабам пиксель-в-пиксель")
    async def test_0155438f_get_progress_exact_json(self):
        with autotest.step("Act: GET /progress"):
            async with self._client() as client:
                resp = await client.get("/progress")

        with autotest.step("Assert: 200 и полный JSON равен ожидаемому"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(
                resp.json(),
                {
                    "courses": [
                        {
                            "id": "cp-1",
                            "course_slug": "networking-101",
                            "status": "in_progress",
                            "score": 42.5,
                            "started_at": "2026-01-01T10:00:00",
                            "completed_at": None,
                        }
                    ],
                    "labs": [
                        {
                            "id": "lp-1",
                            "lab_slug": "ospf-lab",
                            "status": "completed",
                            "score": 100.0,
                            "current_step": 3,
                            "started_at": "2026-01-01T10:00:00",
                            "completed_at": "2026-01-01T11:00:00",
                        }
                    ],
                },
                "полный JSON прогресса",
            )

    @autotest.num("2506")
    @autotest.external_id("2a344044-f0ba-45e3-8cfd-df8eb011ee71")
    @autotest.name("GET /progress/labs/{slug}: полный JSON прогресса лабы с попытками")
    async def test_2a344044_get_lab_progress_exact_json(self):
        with autotest.step("Act: GET /progress/labs/ospf-lab"):
            async with self._client() as client:
                resp = await client.get("/progress/labs/ospf-lab")

        with autotest.step("Assert: 200 и полный JSON равен ожидаемому"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(
                resp.json(),
                {
                    "id": "lp-1",
                    "lab_slug": "ospf-lab",
                    "status": "completed",
                    "score": 100.0,
                    "current_step": 3,
                    "started_at": "2026-01-01T10:00:00",
                    "completed_at": "2026-01-01T11:00:00",
                    "attempts": [
                        {
                            "id": "sa-1",
                            "step_slug": "step-1",
                            "attempt_number": 1,
                            "result": "pass",
                            "score": 100.0,
                            "started_at": "2026-01-01T10:00:00",
                            "ended_at": "2026-01-01T11:00:00",
                        }
                    ],
                },
                "полный JSON прогресса лабы с попытками",
            )

    @autotest.num("2507")
    @autotest.external_id("b628b96a-a6c7-4c6f-8660-a76f406ae2dc")
    @autotest.name("POST /progress/labs/{slug}/start: полный JSON начатого прогресса")
    async def test_b628b96a_start_lab_exact_json(self):
        with autotest.step("Act: POST /progress/labs/bgp-lab/start"):
            async with self._client() as client:
                resp = await client.post("/progress/labs/bgp-lab/start")

        with autotest.step("Assert: 200 и JSON новой записи прогресса лабы"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(
                {k: v for k, v in body.items() if k != "id"},
                {
                    "lab_slug": "bgp-lab",
                    "status": "in_progress",
                    "score": None,
                    "current_step": None,
                    "started_at": body["started_at"],
                    "completed_at": None,
                },
                "поля нового прогресса лабы",
            )
            assert_equal(
                set(body.keys()),
                {
                    "id",
                    "lab_slug",
                    "status",
                    "score",
                    "current_step",
                    "started_at",
                    "completed_at",
                },
                "набор полей ответа",
            )

    @autotest.num("2508")
    @autotest.external_id("d4e4685d-6253-43e2-aeea-fee865fa3616")
    @autotest.name("POST /progress/labs/{slug}/steps/{slug}/attempt: полный JSON попытки")
    async def test_d4e4685d_record_attempt_exact_json(self):
        with autotest.step("Act: POST попытки прохождения шага"):
            async with self._client() as client:
                resp = await client.post(
                    "/progress/labs/ospf-lab/steps/step-2/attempt",
                    json={"result": "fail", "score": 25.0, "error_details": {"reason": "timeout"}},
                )

        with autotest.step("Assert: 200 и JSON новой попытки"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(
                {k: v for k, v in body.items() if k != "id"},
                {
                    "step_slug": "step-2",
                    "attempt_number": 1,
                    "result": "fail",
                    "score": 25.0,
                    "started_at": body["started_at"],
                    "ended_at": None,
                },
                "поля новой попытки (error_details не в ответе)",
            )
            assert_equal(
                set(body.keys()),
                {
                    "id",
                    "step_slug",
                    "attempt_number",
                    "result",
                    "score",
                    "started_at",
                    "ended_at",
                },
                "набор полей ответа",
            )
