# Smoke tests for GET /labs.

import pytest

from autotests.api.api_methods.onlinetlabs_service.labs_api import LabsApi
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_true
from autotests.settings.utils.utils import check_response_status, Randomizer


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestLabsSmokeApi:
    """Smoke tests for GET /labs."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.labs_api = LabsApi(anon_client, config)

    @autotest.num("10")
    @autotest.external_id("ce107529-a0b0-40f6-9a10-4a1fb8f65534")
    @autotest.name("Smoke: GET /labs — 200 and list of labs")
    async def test_ce107529_get_labs(self):
        """Fetching the list of labs returns 200."""
        # Act
        with autotest.step("Send GET /labs"):
            response = await self.labs_api.get_labs()

        # Assert
        with autotest.step("Verify status code 200"):
            check_response_status(response, 200)

        with autotest.step("Verify response is a list"):
            body = response.json()
            assert_true(isinstance(body, list), f"Expected a list, got {type(body)}")

    @autotest.num("11")
    @autotest.external_id("09cf140f-4440-4d96-b46b-ecd9b43e0500")
    @autotest.name("Smoke: GET /labs/{slug} — 404 for nonexistent")
    async def test_09cf140f_get_lab_not_found(self):
        """Requesting a nonexistent lab returns 404."""
        # Arrange
        with autotest.step("Build a nonexistent lab slug"):
            fake_slug = f"nonexistent-{Randomizer.random_string(8).lower()}"

        # Act
        with autotest.step(f"Send GET /labs/{fake_slug}"):
            response = await self.labs_api.get_lab_by_slug(slug=fake_slug)

        # Assert
        with autotest.step("Verify status code 404"):
            check_response_status(response, 404)
