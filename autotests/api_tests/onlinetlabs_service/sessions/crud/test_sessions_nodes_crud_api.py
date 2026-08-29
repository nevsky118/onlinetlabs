# CRUD tests for node actions through the backend.

import asyncio

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_in
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestSessionsNodesCrudApi:
    """CRUD tests for /users/me/sessions/{id}/nodes/*."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("75")
    @autotest.external_id("acb6622b-3eb8-4c78-a392-57c60a41b87d")
    @autotest.name("Sessions CRUD: invalid action 422")
    async def test_acb6622b_invalid_action_422(self):
        """An invalid action results in 422."""
        # Arrange
        with autotest.step("Launch an active session"):
            session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")

        # Act
        with autotest.step("POST per-node with an invalid action=destroy"):
            response = await self.sessions_api.post_node_action(session_id, "any-node-id", "destroy")

        # Assert
        with autotest.step("Check status code 422"):
            check_response_status(response, 422)

    @autotest.num("76")
    @autotest.external_id("be900fe4-4eb4-4a9d-859c-8eea9a634dd3")
    @autotest.name("Sessions CRUD: 12 rapid node actions → 429 present")
    async def test_be900fe4_rate_limit_429(self):
        """slowapi 5/sec, so after a burst of requests we expect 429 in at least one of them."""
        # Arrange
        with autotest.step("Launch an active session and pick a node"):
            session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")
            node_id = await self.sessions_helper.pick_first_node_id(session_id)

        # Act
        with autotest.step("Send 12 POST node action requests in parallel"):
            results = await asyncio.gather(
                *[
                    self.sessions_api.post_node_action(session_id, node_id, "stop")
                    for _ in range(12)
                ],
                return_exceptions=True,
            )

        # Assert
        with autotest.step("Check that 429 appears among the responses"):
            codes = [getattr(result, "status_code", None) for result in results]
            assert_in(429, codes, "429")
