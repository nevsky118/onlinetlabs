import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab, LabStep
from models.user import User
from progress.service import (
    get_all_progress,
    get_lab_progress_detail,
    record_step_attempt,
    start_lab,
)
from tests.report import autotests

pytestmark = pytest.mark.progress


class TestStartLab:
    @autotests.num("120")
    @autotests.external_id("progress-service-start-lab-new")
    @autotests.name("start_lab: создание нового прогресса")
    async def test_creates_progress(
        self, db_session: AsyncSession, progress_user: User, progress_lab: Lab
    ):
        with autotests.step("Начинаем лабу"):
            lp = await start_lab(db_session, progress_user.id, progress_lab.slug)

        with autotests.step("Проверяем прогресс"):
            assert lp.user_id == progress_user.id
            assert lp.lab_slug == progress_lab.slug
            assert lp.status == "in_progress"
            assert lp.started_at is not None

    @autotests.num("121")
    @autotests.external_id("progress-service-start-lab-idempotent")
    @autotests.name("start_lab: идемпотентность")
    async def test_idempotent(
        self, db_session: AsyncSession, progress_user: User, progress_lab: Lab
    ):
        with autotests.step("Начинаем лабу дважды"):
            lp1 = await start_lab(db_session, progress_user.id, progress_lab.slug)
            lp2 = await start_lab(db_session, progress_user.id, progress_lab.slug)

        with autotests.step("Проверяем что тот же объект"):
            assert lp1.id == lp2.id


class TestRecordStepAttempt:
    @autotests.num("122")
    @autotests.external_id("progress-service-record-attempt")
    @autotests.name("record_step_attempt: запись попытки")
    async def test_records_attempt(
        self,
        db_session: AsyncSession,
        progress_user: User,
        progress_lab: Lab,
        progress_lab_steps: list[LabStep],
    ):
        with autotests.step("Записываем первую попытку"):
            a1 = await record_step_attempt(
                db_session, progress_user.id, progress_lab.slug, "ps-1", result="fail"
            )

        with autotests.step("Проверяем attempt_number=1"):
            assert a1.attempt_number == 1
            assert a1.result == "fail"

        with autotests.step("Записываем вторую попытку"):
            a2 = await record_step_attempt(
                db_session,
                progress_user.id,
                progress_lab.slug,
                "ps-1",
                result="pass",
                score=100.0,
            )

        with autotests.step("Проверяем attempt_number=2"):
            assert a2.attempt_number == 2
            assert a2.score == 100.0


class TestGetAllProgress:
    @autotests.num("123")
    @autotests.external_id("progress-service-get-all")
    @autotests.name("get_all_progress: возвращает прогресс пользователя")
    async def test_returns_progress(
        self, db_session: AsyncSession, progress_user: User, progress_lab: Lab
    ):
        with autotests.step("Создаём прогресс"):
            await start_lab(db_session, progress_user.id, progress_lab.slug)

        with autotests.step("Запрашиваем весь прогресс"):
            result = await get_all_progress(db_session, progress_user.id)

        with autotests.step("Проверяем лабы в результате"):
            assert len(result["labs"]) >= 1
            assert result["labs"][0].lab_slug == progress_lab.slug


class TestGetLabProgressDetail:
    @autotests.num("124")
    @autotests.external_id("progress-service-get-detail")
    @autotests.name("get_lab_progress_detail: детальный прогресс с попытками")
    async def test_returns_detail(
        self,
        db_session: AsyncSession,
        progress_user: User,
        progress_lab: Lab,
        progress_lab_steps: list[LabStep],
    ):
        with autotests.step("Создаём прогресс и попытку"):
            await start_lab(db_session, progress_user.id, progress_lab.slug)
            await record_step_attempt(
                db_session, progress_user.id, progress_lab.slug, "ps-1", result="pass"
            )

        with autotests.step("Запрашиваем детальный прогресс"):
            detail = await get_lab_progress_detail(
                db_session, progress_user.id, progress_lab.slug
            )

        with autotests.step("Проверяем прогресс и попытки"):
            assert detail is not None
            assert detail["progress"].lab_slug == progress_lab.slug
            assert len(detail["attempts"]) == 1
