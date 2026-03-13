# Smoke-тесты GET /labs.

import pytest

from autotests.api.api_methods.onlinetlabs_service.labs_api import LabsApi
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_true
from autotests.settings.utils.utils import check_response_status, Randomizer


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestLabsSmokeApi:
    """Smoke-тесты GET /labs."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.labs_api = LabsApi(anon_client, config)

    @autotest.num("10")
    @autotest.external_id("d0e1f2a3-b4c5-6789-defa-890123456789")
    @autotest.name("Smoke: GET /labs — 200 и список лабораторий")
    async def test_d0e1f2a3_get_labs(self):
        """Получение списка лабораторий возвращает 200."""
        # Act
        with autotest.step("Отправляем GET /labs"):
            response = await self.labs_api.get_labs()

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

        with autotest.step("Проверяем, что ответ — список"):
            body = response.json()
            assert_true(isinstance(body, list), f"Ожидался список, получен {type(body)}")

    @autotest.num("11")
    @autotest.external_id("e1f2a3b4-c5d6-7890-efab-901234567890")
    @autotest.name("Smoke: GET /labs/{slug} — 404 для несуществующей")
    async def test_e1f2a3b4_get_lab_not_found(self):
        """Запрос несуществующей лабораторной возвращает 404."""
        # Arrange
        fake_slug = f"nonexistent-{Randomizer.random_string(8).lower()}"

        # Act
        with autotest.step(f"Отправляем GET /labs/{fake_slug}"):
            response = await self.labs_api.get_lab_by_slug(slug=fake_slug)

        # Assert
        with autotest.step("Проверяем статус код 404"):
            check_response_status(response, 404)
