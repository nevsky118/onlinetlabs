# Smoke tests for /users/me/progress.

import pytest

from autotests.api.api_methods.onlinetlabs_service.progress_api import ProgressApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status, Randomizer


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestProgressSmokeApi:
    """Smoke tests for /users/me/progress."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.progress_api = ProgressApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)

    @autotest.num("14")
    @autotest.external_id("820270ea-61fd-4720-a308-b1d36d44f448")
    @autotest.name("Smoke: GET /users/me/progress — 200")
    async def test_820270ea_get_progress(self):
        """Fetching the progress returns 200."""
        # Act
        with autotest.step("Send GET /users/me/progress"):
            response = await self.progress_api.get_progress()

        # Assert
        with autotest.step("Check status code 200"):
            check_response_status(response, 200)

    @autotest.num("15")
    @autotest.external_id("0472dcf0-378b-49fa-b920-9119bacf67a9")
    @autotest.name("Smoke: GET /users/me/progress/labs/{slug} — 404 for a nonexistent lab")
    async def test_0472dcf0_get_lab_progress_not_found(self):
        """Progress for a nonexistent lab returns 404."""
        # Arrange
        with autotest.step("Build a nonexistent lab slug"):
            fake_slug = f"nonexistent-{Randomizer.random_string(8).lower()}"

        # Act
        with autotest.step(f"Send GET /users/me/progress/labs/{fake_slug}"):
            response = await self.progress_api.get_lab_progress(lab_slug=fake_slug)

        # Assert
        with autotest.step("Check status code 404"):
            check_response_status(response, 404)
