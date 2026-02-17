import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from labs.service import get_all_labs, get_lab_by_slug
from models.course import Course
from models.lab import Lab
from tests.report import autotests

pytestmark = pytest.mark.labs


class TestGetAllLabs:
    @autotests.num("110")
    @autotests.external_id("labs-service-get-all")
    @autotests.name("get_all_labs: возвращает лабы")
    async def test_returns_labs(
        self, db_session: AsyncSession, sample_lab: Lab, sample_standalone_lab: Lab
    ):
        with autotests.step("Запрашиваем все лабы"):
            labs = await get_all_labs(db_session)

        with autotests.step("Проверяем что обе лабы присутствуют"):
            slugs = [lab.slug for lab in labs]
            assert "lab-traceroute" in slugs
            assert "lab-standalone" in slugs

    @autotests.num("111")
    @autotests.external_id("labs-service-filter-by-course")
    @autotests.name("get_all_labs: фильтрация по курсу")
    async def test_filter_by_course(
        self,
        db_session: AsyncSession,
        sample_lab: Lab,
        sample_standalone_lab: Lab,
        sample_course_for_labs: Course,
    ):
        with autotests.step("Запрашиваем лабы курса net-201"):
            labs = await get_all_labs(
                db_session, course_slug=sample_course_for_labs.slug
            )

        with autotests.step("Проверяем что только лаба курса"):
            assert len(labs) == 1
            assert labs[0].slug == "lab-traceroute"


class TestGetLabBySlug:
    @autotests.num("112")
    @autotests.external_id("labs-service-get-by-slug-found")
    @autotests.name("get_lab_by_slug: найдена со степами")
    async def test_found_with_steps(self, db_session: AsyncSession, sample_lab: Lab):
        with autotests.step("Запрашиваем лабу по slug"):
            lab = await get_lab_by_slug(db_session, "lab-traceroute")

        with autotests.step("Проверяем лабу и степы"):
            assert lab is not None
            assert lab.slug == "lab-traceroute"
            assert len(lab.steps) == 2

    @autotests.num("113")
    @autotests.external_id("labs-service-get-by-slug-not-found")
    @autotests.name("get_lab_by_slug: не найдена")
    async def test_not_found(self, db_session: AsyncSession):
        with autotests.step("Запрашиваем несуществующую лабу"):
            lab = await get_lab_by_slug(db_session, "nonexistent")

        with autotests.step("Проверяем None"):
            assert lab is None
