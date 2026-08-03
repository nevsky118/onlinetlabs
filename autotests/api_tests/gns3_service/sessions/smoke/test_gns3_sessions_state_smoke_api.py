# Smoke tests for GET /sessions/{id}/state in gns3-service.

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_in, assert_is_not_none
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestGns3SessionsStateSmokeApi:
    """Smoke tests for GET /sessions/{id}/state in gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.config = config
        self.gns3_sessions_api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)

    @autotest.num("160")
    @autotest.external_id("c5d668a0-6a77-4f38-9c27-895e157a1866")
    @autotest.name("Gns3 Smoke: GET /sessions/{id}/state — 200")
    async def test_c5d668a0_state_200(self):
        """GET /sessions/{id}/state returns 200 for an active session."""
        # Arrange
        with autotest.step("Create GNS3 session"):
            session_dict = await self.gns3_sessions_helper.create_session()
            session_id = session_dict["session_id"]

        # Act
        with autotest.step("Request session state"):
            response = await self.gns3_sessions_api.get_state(session_id)

        # Assert
        with autotest.step("Verify status code 200"):
            check_response_status(response, 200)

    @autotest.num("161")
    @autotest.external_id("04a1ce6a-8f6b-4fd6-89b6-90fd961f93bd")
    @autotest.name("Gns3 Smoke: state contains nodes/links/metrics")
    async def test_04a1ce6a_state_shape(self):
        """The state response contains the fields nodes, links, metrics."""
        # Arrange
        with autotest.step("Create GNS3 session"):
            session_dict = await self.gns3_sessions_helper.create_session()
            session_id = session_dict["session_id"]

        # Act
        with autotest.step("Get session state"):
            body = await self.gns3_sessions_helper.get_state_and_verify(session_id)

        # Assert
        with autotest.step("Verify response structure"):
            assert_is_not_none(body.get("session_id"), "session_id missing")
            assert_in("nodes", body, "nodes field missing")
            assert_in("links", body, "links field missing")
            assert_in("metrics", body, "metrics field missing")
            assert_in("nodes_total", body["metrics"], "metrics.nodes_total missing")
