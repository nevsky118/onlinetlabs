import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.lab import Lab
from models.progress import LabProgress
from models.user import User
from progress.service import record_lab_validation, score_from_steps

pytestmark = [pytest.mark.unit]


def _steps(*step_specs: list[bool]) -> list[dict]:
    """Строит steps-снимок: каждый аргумент — список ok-флагов проверок шага."""
    return [
        {
            "id": f"s{i}",
            "title": f"Step {i}",
            "ok": all(checks),
            "checks": [{"kind": "x", "ok": ok} for ok in checks],
        }
        for i, checks in enumerate(step_specs)
    ]


class TestScoreFromSteps:
    @autotest.num("760")
    @autotest.external_id("d1a2b3c4-e5f6-4708-8901-bbccddee0001")
    @autotest.name("score_from_steps: доля пройденных проверок, полное прохождение")
    def test_all_checks_passed(self):
        with autotest.step("Act: 2 шага по 2 успешных проверки"):
            score, all_passed = score_from_steps(_steps([True, True], [True, True]))
        with autotest.step("Assert: 100 и all_passed"):
            assert_equal(score, 100.0, "score")
            assert_true(all_passed, "all_passed")

    @autotest.num("761")
    @autotest.external_id("d1a2b3c4-e5f6-4708-8901-bbccddee0002")
    @autotest.name("score_from_steps: частичное — 3 из 4 проверок = 75")
    def test_partial_checks(self):
        with autotest.step("Act: 3 из 4 проверок пройдены"):
            score, all_passed = score_from_steps(_steps([True, True], [True, False]))
        with autotest.step("Assert: 75 и не all_passed"):
            assert_equal(score, 75.0, "score")
            assert_true(not all_passed, "not all_passed")

    @autotest.num("762")
    @autotest.external_id("d1a2b3c4-e5f6-4708-8901-bbccddee0003")
    @autotest.name("score_from_steps: нет шагов → 0 и не пройдено")
    def test_no_steps(self):
        with autotest.step("Act: пустой список"):
            score, all_passed = score_from_steps([])
        with autotest.step("Assert: 0.0, not all_passed"):
            assert_equal(score, 0.0, "score")
            assert_true(not all_passed, "not all_passed")


class TestRecordLabValidation:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LabProgress.__table__.create)
        async with self.session_factory() as db:
            db.add_all(
                [
                    User(id="u1", email="u1@test.local", role="student"),
                    Lab(slug="dhcp-basics", title="DHCP Basics"),
                ]
            )
            await db.commit()
        yield
        await self.engine.dispose()

    async def _get(self) -> LabProgress:
        async with self.session_factory() as db:
            r = await db.execute(select(LabProgress).where(LabProgress.user_id == "u1"))
            return r.scalar_one()

    @autotest.num("763")
    @autotest.external_id("d1a2b3c4-e5f6-4708-8901-bbccddee0010")
    @autotest.name("record_lab_validation: полное прохождение → completed, score 100")
    async def test_full_pass_marks_completed(self):
        with autotest.step("Act: записываем полный успех"):
            async with self.session_factory() as db:
                await record_lab_validation(db, "u1", "dhcp-basics", _steps([True, True], [True]))
        with autotest.step("Assert: completed, score 100, есть completed_at"):
            lp = await self._get()
            assert_equal(lp.status, "completed", "status")
            assert_equal(lp.score, 100.0, "score")
            assert_true(lp.completed_at is not None, "completed_at установлен")

    @autotest.num("764")
    @autotest.external_id("d1a2b3c4-e5f6-4708-8901-bbccddee0011")
    @autotest.name("record_lab_validation: частично → in_progress, дробная оценка")
    async def test_partial_stays_in_progress(self):
        with autotest.step("Act: 1 из 2 проверок"):
            async with self.session_factory() as db:
                await record_lab_validation(db, "u1", "dhcp-basics", _steps([True, False]))
        with autotest.step("Assert: in_progress, score 50, без completed_at"):
            lp = await self._get()
            assert_equal(lp.status, "in_progress", "status")
            assert_equal(lp.score, 50.0, "score")
            assert_true(lp.completed_at is None, "completed_at пуст")

    @autotest.num("765")
    @autotest.external_id("d1a2b3c4-e5f6-4708-8901-bbccddee0012")
    @autotest.name("record_lab_validation: лучшая оценка сохраняется, completed не сбрасывается")
    async def test_best_score_kept_and_completed_sticky(self):
        with autotest.step("Arrange: сначала полный успех"):
            async with self.session_factory() as db:
                await record_lab_validation(db, "u1", "dhcp-basics", _steps([True], [True]))
        with autotest.step("Act: затем неудачный повтор (1 из 2)"):
            async with self.session_factory() as db:
                await record_lab_validation(db, "u1", "dhcp-basics", _steps([True, False]))
        with autotest.step("Assert: остаётся completed и score 100"):
            lp = await self._get()
            assert_equal(lp.status, "completed", "status остаётся completed")
            assert_equal(lp.score, 100.0, "лучшая оценка сохранена")
