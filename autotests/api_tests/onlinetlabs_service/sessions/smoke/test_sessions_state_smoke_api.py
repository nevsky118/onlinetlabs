# Smoke-тесты GET /users/me/sessions/{id}/state.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_in, assert_is_not_none
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestSessionsStateSmokeApi:
    """Smoke-тесты /users/me/sessions/{id}/state."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("70")
    @autotest.external_id("70111111-7777-4777-7777-777777777777")
    @autotest.name("Sessions Smoke: GET .../state — 200")
    async def test_70111111_state_200(self):
        """GET state активной сессии возвращает 200 и обязательные поля."""
        # Arrange
        session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")

        # Act
        with autotest.step(f"GET /users/me/sessions/{session_id}/state"):
            response = await self.sessions_api.get_session_state(session_id)

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

        with autotest.step("Проверяем наличие sessionId, nodes, metrics в ответе"):
            body = response.json()
            assert_is_not_none(body.get("sessionId"), "sessionId отсутствует")
            assert_in("nodes", body, "поле nodes отсутствует")
            assert_in("metrics", body, "поле metrics отсутствует")
