# Smoke test for fetching a session by id, GET /users/me/sessions/{session_id}.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestSessionsGetSmokeApi:
    """Smoke test for GET /users/me/sessions/{session_id}."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("60")
    @autotest.external_id("bbf2082f-f5e8-4e36-9eb4-bf17ee724e26")
    @autotest.name("Smoke: GET /users/me/sessions/{id} — 200, body contains lab_slug and status")
    async def test_bbf2082f_get_session_by_id(self):
        """GET by id returns 200 with the lab_slug and status of the launched session."""
        with autotest.step("Launch the autotest-lab session"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        with autotest.step("Fetch the session by id"):
            response = await self.sessions_api.get_session(session_id)

        with autotest.step("Check status code 200"):
            check_response_status(response, 200)
            body = response.json()

        with autotest.step("Check lab_slug"):
            assert body.get("lab_slug") == "autotest-lab", f"Expected lab_slug=autotest-lab, got: {body.get('lab_slug')}"

        with autotest.step("Check status=active"):
            assert body.get("status") == "active", f"Expected status=active, got: {body.get('status')}"

        with autotest.step("Check lab_title"):
            assert body.get("lab_title") == "Autotest Lab", f"Expected lab_title=Autotest Lab, got: {body.get('lab_title')}"
