# Smoke tests for /users/me/sessions.

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
    """Smoke tests for /users/me/sessions."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("12")
    @autotest.external_id("983da460-2816-4f71-b5b1-af3d8e853d36")
    @autotest.name("Smoke: GET /users/me/sessions — 200")
    async def test_983da460_get_sessions(self):
        """Fetching the list of sessions returns 200."""
        # Act
        with autotest.step("Send GET /users/me/sessions"):
            response = await self.sessions_api.get_sessions()

        # Assert
        with autotest.step("Check status code 200"):
            check_response_status(response, 200)

    @autotest.num("13")
    @autotest.external_id("a2611deb-8eb6-44c3-a8ab-317537296240")
    @autotest.name("Smoke: POST /users/me/sessions — 201 session creation")
    async def test_a2611deb_create_session(self):
        """Creating a session returns 201."""
        # Arrange
        with autotest.step("Build session create data"):
            session_data = SessionCreateData(lab_slug="autotest-lab")

        # Act
        with autotest.step("Create the session"):
            response = await self.sessions_api.post_session(data=session_data.data)

        # Assert
        with autotest.step("Check status code 201"):
            check_response_status(response, 201)

        with autotest.step("Check session_id is present in the response"):
            body = response.json()
            assert_is_not_none(body.get("session_id"), "session's session_id must not be None")
