# Smoke tests for GET /courses.

import pytest

from autotests.api.api_methods.onlinetlabs_service.courses_api import CoursesApi
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_true
from autotests.settings.utils.utils import check_response_status, Randomizer


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestCoursesSmokeApi:
    """Smoke tests for GET /courses."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.courses_api = CoursesApi(anon_client, config)

    @autotest.num("8")
    @autotest.external_id("b8c9d0e1-f2a3-4567-bcde-678901234567")
    @autotest.name("Smoke: GET /courses — 200 and list of courses")
    async def test_b8c9d0e1_get_courses(self):
        """Fetching the list of courses returns 200."""
        # Act
        with autotest.step("Send GET /courses"):
            response = await self.courses_api.get_courses()

        # Assert
        with autotest.step("Verify status code 200"):
            check_response_status(response, 200)

        with autotest.step("Verify response is a list"):
            body = response.json()
            assert_true(isinstance(body, list), f"Expected a list, got {type(body)}")

    @autotest.num("9")
    @autotest.external_id("34a114c2-ad3c-4856-9837-760a70ff7175")
    @autotest.name("Smoke: GET /courses/{slug} — 404 for nonexistent")
    async def test_34a114c2_get_course_not_found(self):
        """Requesting a nonexistent course returns 404."""
        # Arrange
        with autotest.step("Build a nonexistent course slug"):
            fake_slug = f"nonexistent-{Randomizer.random_string(8).lower()}"

        # Act
        with autotest.step(f"Send GET /courses/{fake_slug}"):
            response = await self.courses_api.get_course_by_slug(slug=fake_slug)

        # Assert
        with autotest.step("Verify status code 404"):
            check_response_status(response, 404)
