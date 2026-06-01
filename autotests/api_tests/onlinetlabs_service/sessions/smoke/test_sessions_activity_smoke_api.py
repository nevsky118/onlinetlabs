# Smoke-тесты GET activity через backend.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.api.data.onlinetlabs_service.sessions_data_api import ActivityQueryData
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_in
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestSessionsActivitySmokeApi:
    """Smoke-тесты /users/me/sessions/{id}/activity."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("73")
    @autotest.external_id("73111111-7777-4777-7777-777777777777")
    @autotest.name("Sessions Smoke: GET .../activity — 200")
    async def test_73111111_activity_200(self):
        """GET activity возвращает 200 и поля events/nextCursor."""
        # Arrange
        session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")
        query = ActivityQueryData(limit=10)

        # Act
        with autotest.step(f"GET .../sessions/{session_id}/activity"):
            response = await self.sessions_api.get_session_activity(session_id, query.data)

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

        with autotest.step("Проверяем наличие полей events и nextCursor"):
            body = response.json()
            assert_in("events", body, "поле events отсутствует")
            assert_in("nextCursor", body, "поле nextCursor отсутствует")
