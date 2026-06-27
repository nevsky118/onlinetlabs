# CRUD-тесты /users/me/preferences.

import pytest

from autotests.api.api_methods.onlinetlabs_service.preferences_api import PreferencesApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestPreferencesCrudApi:
    """CRUD-тесты /users/me/preferences."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.preferences_api = PreferencesApi(
            anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT
        )

    @autotest.num("803")
    @autotest.external_id("bbaf4a63-0451-480f-8dff-4f2b491c93b4")
    @autotest.name("CRUD: PATCH /users/me/preferences — выбор модели без права → 403")
    async def test_bbaf4a63_set_model_without_permission_forbidden(self):
        """Установка модели аккаунтом без права выбора возвращает 403."""
        # Act
        with autotest.step("PATCH default_model_id для аккаунта без can_select"):
            response = await self.preferences_api.patch_preferences(
                {"default_model_id": "yandex-gpt-5.1"}
            )

        # Assert
        with autotest.step("Проверяем статус код 403"):
            check_response_status(response, 403)
