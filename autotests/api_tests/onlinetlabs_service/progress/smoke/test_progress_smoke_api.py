# Smoke-тесты /users/me/progress.

import pytest

from autotests.api.api_methods.onlinetlabs_service.progress_api import ProgressApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status, Randomizer


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestProgressSmokeApi:
    """Smoke-тесты /users/me/progress."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.progress_api = ProgressApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)

    @autotest.num("14")
    @autotest.external_id("b4c5d6e7-f8a9-0123-bcde-234567890123")
    @autotest.name("Smoke: GET /users/me/progress — 200")
    async def test_b4c5d6e7_get_progress(self):
        """Получение прогресса возвращает 200."""
        # Act
        with autotest.step("Отправляем GET /users/me/progress"):
            response = await self.progress_api.get_progress()

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

    @autotest.num("15")
    @autotest.external_id("c5d6e7f8-a9b0-1234-cdef-345678901234")
    @autotest.name("Smoke: GET /users/me/progress/labs/{slug} — 404 для несуществующей")
    async def test_c5d6e7f8_get_lab_progress_not_found(self):
        """Прогресс по несуществующей лабораторной возвращает 404."""
        # Arrange
        fake_slug = f"nonexistent-{Randomizer.random_string(8).lower()}"

        # Act
        with autotest.step(f"Отправляем GET /users/me/progress/labs/{fake_slug}"):
            response = await self.progress_api.get_lab_progress(lab_slug=fake_slug)

        # Assert
        with autotest.step("Проверяем статус код 404"):
            check_response_status(response, 404)
