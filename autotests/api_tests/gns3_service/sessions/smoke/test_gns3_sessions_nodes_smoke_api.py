"""Smoke node actions — gns3-service."""

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestGns3SessionsNodesSmokeApi:
    """Smoke /sessions/{id}/nodes/* — gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.gns3_sessions_api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)

    @autotest.num("163")
    @autotest.external_id("87d65555-e213-4a66-9dbe-2888d62b75ba")
    @autotest.name("Gns3 Smoke: POST .../nodes/{id}/stop — 204")
    async def test_87d65555_node_stop_204(self):
        """Stopping a single node returns 204."""
        with autotest.step("Arrange: create a session and pick a node"):
            session_dict = await self.gns3_sessions_helper.create_session()
            session_id = session_dict["session_id"]
            node_id = await self.gns3_sessions_helper.pick_first_node_id(session_id)

        with autotest.step("Act: stop the node"):
            response = await self.gns3_sessions_api.post_node_action(session_id, node_id, "stop")
        with autotest.step("Assert: 204"):
            check_response_status(response, 204)

    @autotest.num("164")
    @autotest.external_id("638082ba-5f82-4b1c-ae49-8aaf14210411")
    @autotest.name("Gns3 Smoke: POST .../nodes/stop (bulk) — 204")
    async def test_638082ba_bulk_stop_204(self):
        """Bulk-stopping all nodes returns 204."""
        with autotest.step("Arrange: create a session"):
            session_dict = await self.gns3_sessions_helper.create_session()
            session_id = session_dict["session_id"]

        with autotest.step("Act: bulk-stop all nodes"):
            response = await self.gns3_sessions_api.post_bulk_node_action(session_id, "stop")
        with autotest.step("Assert: 204"):
            check_response_status(response, 204)
