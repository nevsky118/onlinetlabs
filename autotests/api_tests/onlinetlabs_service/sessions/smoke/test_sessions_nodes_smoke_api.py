# Smoke tests for POST node actions through the backend.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestSessionsNodesSmokeApi:
    """Smoke tests for /users/me/sessions/{id}/nodes/*."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("71")
    @autotest.external_id("b16604f8-4af1-4da5-afb8-2102ac2b417c")
    @autotest.name("Sessions Smoke: POST .../nodes/{id}/stop — 200")
    async def test_b16604f8_node_stop_200(self):
        """POST per-node stop returns 200."""
        # Arrange
        with autotest.step("Launch an active session and pick a node"):
            session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")
            node_id = await self.sessions_helper.pick_first_node_id(session_id)

        # Act
        with autotest.step(f"POST .../sessions/{session_id}/nodes/{node_id}/stop"):
            response = await self.sessions_api.post_node_action(session_id, node_id, "stop")

        # Assert
        with autotest.step("Check status code 200"):
            check_response_status(response, 200)

    @autotest.num("72")
    @autotest.external_id("06d28ea6-b109-4dc5-b6ea-ffb767f3786d")
    @autotest.name("Sessions Smoke: POST .../nodes/stop (bulk) — 200")
    async def test_06d28ea6_bulk_stop_200(self):
        """POST bulk stop returns 200."""
        # Arrange
        with autotest.step("Launch an active session"):
            session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")

        # Act
        with autotest.step(f"POST .../sessions/{session_id}/nodes/stop"):
            response = await self.sessions_api.post_bulk_node_action(session_id, "stop")

        # Assert
        with autotest.step("Check status code 200"):
            check_response_status(response, 200)
