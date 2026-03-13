# Smoke-тесты GET /courses.

import pytest

from autotests.api.api_methods.onlinetlabs_service.courses_api import CoursesApi
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_true
from autotests.settings.utils.utils import check_response_status, Randomizer


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestCoursesSmokeApi:
    """Smoke-тесты GET /courses."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.courses_api = CoursesApi(anon_client, config)

    @autotest.num("8")
    @autotest.external_id("b8c9d0e1-f2a3-4567-bcde-678901234567")
    @autotest.name("Smoke: GET /courses — 200 и список курсов")
    async def test_b8c9d0e1_get_courses(self):
        """Получение списка курсов возвращает 200."""
        # Act
        with autotest.step("Отправляем GET /courses"):
            response = await self.courses_api.get_courses()

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

        with autotest.step("Проверяем, что ответ — список"):
            body = response.json()
            assert_true(isinstance(body, list), f"Ожидался список, получен {type(body)}")

    @autotest.num("9")
    @autotest.external_id("c9d0e1f2-a3b4-5678-cdef-789012345678")
    @autotest.name("Smoke: GET /courses/{slug} — 404 для несуществующего")
    async def test_c9d0e1f2_get_course_not_found(self):
        """Запрос несуществующего курса возвращает 404."""
        # Arrange
        fake_slug = f"nonexistent-{Randomizer.random_string(8).lower()}"

        # Act
        with autotest.step(f"Отправляем GET /courses/{fake_slug}"):
            response = await self.courses_api.get_course_by_slug(slug=fake_slug)

        # Assert
        with autotest.step("Проверяем статус код 404"):
            check_response_status(response, 404)
