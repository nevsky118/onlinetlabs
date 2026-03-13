# Smoke-тесты /users/me/sessions.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.api.data.onlinetlabs_service.sessions_data_api import SessionCreateData
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_is_not_none
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestSessionsSmokeApi:
    """Smoke-тесты /users/me/sessions."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("12")
    @autotest.external_id("f2a3b4c5-d6e7-8901-fabc-012345678901")
    @autotest.name("Smoke: GET /users/me/sessions — 200")
    async def test_f2a3b4c5_get_sessions(self):
        """Получение списка сессий возвращает 200."""
        # Act
        with autotest.step("Отправляем GET /users/me/sessions"):
            response = await self.sessions_api.get_sessions()

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

    @autotest.num("13")
    @autotest.external_id("a3b4c5d6-e7f8-9012-abcd-123456789012")
    @autotest.name("Smoke: POST /users/me/sessions — 201 создание сессии")
    async def test_a3b4c5d6_create_session(self):
        """Создание сессии возвращает 201."""
        # Arrange
        session_data = SessionCreateData(lab_slug="autotest-lab")

        # Act
        with autotest.step("Создаём сессию"):
            response = await self.sessions_api.post_session(data=session_data.data)

        # Assert
        with autotest.step("Проверяем статус код 201"):
            check_response_status(response, 201)

        with autotest.step("Проверяем наличие id в ответе"):
            body = response.json()
            assert_is_not_none(body.get("id"), "id сессии не должен быть None")
