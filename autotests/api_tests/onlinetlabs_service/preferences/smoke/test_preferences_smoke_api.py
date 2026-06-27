# Smoke-тесты /users/me/preferences.

import pytest

from autotests.api.api_methods.onlinetlabs_service.preferences_api import PreferencesApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_in, assert_is_none
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestPreferencesSmokeApi:
    """Smoke-тесты /users/me/preferences."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.preferences_api = PreferencesApi(
            anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT
        )

    @autotest.num("801")
    @autotest.external_id("c1edee66-bbdc-492f-9521-8f573a0725a6")
    @autotest.name("Smoke: GET /users/me/preferences — 200")
    async def test_c1edee66_get_preferences(self):
        """Чтение настроек возвращает 200 с полем default_model_id."""
        # Act
        with autotest.step("Отправляем GET /users/me/preferences"):
            response = await self.preferences_api.get_preferences()

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)
        with autotest.step("Проверяем наличие поля default_model_id"):
            assert_in(
                "default_model_id",
                response.json(),
                "поле default_model_id присутствует",
            )

    @autotest.num("802")
    @autotest.external_id("d924753b-1a0f-4006-9eca-231618d7f838")
    @autotest.name("Smoke: PATCH /users/me/preferences — очистка модели (200)")
    async def test_d924753b_clear_default_model(self):
        """Очистка модели по умолчанию (null) доступна всем и возвращает 200."""
        # Act
        with autotest.step("Отправляем PATCH default_model_id=null"):
            response = await self.preferences_api.patch_preferences(
                {"default_model_id": None}
            )

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)
        with autotest.step("Проверяем, что default_model_id очищен (null)"):
            assert_is_none(
                response.json()["default_model_id"], "default_model_id == null"
            )
