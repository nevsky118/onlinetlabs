# Smoke tests for GET /users/me/sessions/{id}/state.

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
    """Smoke tests for /users/me/sessions/{id}/state."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("70")
    @autotest.external_id("5f19b9b3-f41f-4ab5-9f8b-8ab06d8e2594")
    @autotest.name("Sessions Smoke: GET .../state — 200")
    async def test_5f19b9b3_state_200(self):
        """GET state of an active session returns 200 and the required fields."""
        # Arrange
        with autotest.step("Launch an active session"):
            session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")

        # Act
        with autotest.step(f"GET /users/me/sessions/{session_id}/state"):
            response = await self.sessions_api.get_session_state(session_id)

        # Assert
        with autotest.step("Check status code 200"):
            check_response_status(response, 200)

        with autotest.step("Check sessionId, nodes, metrics are present in the response"):
            body = response.json()
            assert_is_not_none(body.get("sessionId"), "sessionId is missing")
            assert_in("nodes", body, "field nodes is missing")
            assert_in("metrics", body, "field metrics is missing")
