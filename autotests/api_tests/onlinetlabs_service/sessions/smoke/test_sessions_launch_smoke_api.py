# Smoke tests for session launch /users/me/sessions (launch lifecycle).

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_is_not_none
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestSessionsLaunchSmokeApi:
    """Smoke tests for launching a lab session via /users/me/sessions."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("50")
    @autotest.external_id("799f4ee4-15a4-4af3-9933-f9891b252bf8")
    @autotest.name("Smoke: POST /users/me/sessions — 201 launch autotest-lab, body contains session_id/gns3_*/status=active")
    async def test_799f4ee4_launch_autotest_lab(self):
        """Launching autotest-lab returns 201 with a full response body and status=active."""
        # Act
        with autotest.step("Launch the session for autotest-lab via the helper"):
            body = await self.sessions_helper.launch_session("autotest-lab")

        # Assert
        with autotest.step("Check session_id is present"):
            assert_is_not_none(body.get("session_id"), "session_id must not be None")

        with autotest.step("Check status=active"):
            assert body.get("status") == "active", f"Expected status=active, got: {body.get('status')}"

        with autotest.step("Check gns3_username is present"):
            assert_is_not_none(body.get("gns3_username"), "gns3_username must not be None")

        with autotest.step("Check gns3_password is present"):
            assert_is_not_none(body.get("gns3_password"), "gns3_password must not be None")

        with autotest.step("Check gns3_url is present"):
            assert_is_not_none(body.get("gns3_url"), "gns3_url must not be None")

        with autotest.step("Check gns3_url uses a public host, not Docker-internal"):
            assert "gns3-server" not in body["gns3_url"], (
                f"gns3_url must be browser-reachable (public), got: {body['gns3_url']}"
            )
