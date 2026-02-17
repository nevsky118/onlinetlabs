import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from courses.service import get_all_courses, get_course_by_slug
from models.course import Course
from models.lab import Lab
from tests.report import autotests

pytestmark = pytest.mark.courses


class TestGetAllCourses:
    @autotests.num("100")
    @autotests.external_id("courses-service-get-all")
    @autotests.name("get_all_courses: возвращает курсы")
    async def test_returns_courses(
        self, db_session: AsyncSession, sample_course: Course
    ):
        with autotests.step("Запрашиваем все курсы"):
            courses = await get_all_courses(db_session)

        with autotests.step("Проверяем что курс присутствует"):
            assert len(courses) >= 1
            slugs = [c.slug for c in courses]
            assert "net-101" in slugs

    @autotests.num("101")
    @autotests.external_id("courses-service-get-all-empty")
    @autotests.name("get_all_courses: пустой список")
    async def test_returns_empty(self, db_session: AsyncSession):
        with autotests.step("Запрашиваем курсы из пустой БД"):
            courses = await get_all_courses(db_session)

        with autotests.step("Проверяем пустой список"):
            assert courses == []


class TestGetCourseBySlug:
    @autotests.num("102")
    @autotests.external_id("courses-service-get-by-slug-found")
    @autotests.name("get_course_by_slug: найден с лабами")
    async def test_found_with_labs(
        self, db_session: AsyncSession, sample_course: Course, sample_lab_in_course: Lab
    ):
        with autotests.step("Запрашиваем курс по slug"):
            course = await get_course_by_slug(db_session, "net-101")

        with autotests.step("Проверяем курс и его лабы"):
            assert course is not None
            assert course.slug == "net-101"
            assert len(course.labs) == 1
            assert course.labs[0].slug == "lab-ping"

    @autotests.num("103")
    @autotests.external_id("courses-service-get-by-slug-not-found")
    @autotests.name("get_course_by_slug: не найден")
    async def test_not_found(self, db_session: AsyncSession):
        with autotests.step("Запрашиваем несуществующий курс"):
            course = await get_course_by_slug(db_session, "nonexistent")

        with autotests.step("Проверяем None"):
            assert course is None
