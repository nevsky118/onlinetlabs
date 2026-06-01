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
    @autotest.external_id("c1111111-cccc-4ccc-cccc-cccccccccccc")
    @autotest.name("Gns3 Smoke: POST .../nodes/{id}/stop — 204")
    async def test_c1111111_node_stop_204(self):
        """Остановка одного узла возвращает 204."""
        session_dict = await self.gns3_sessions_helper.create_session()
        session_id = session_dict["session_id"]
        node_id = await self.gns3_sessions_helper.pick_first_node_id(session_id)

        response = await self.gns3_sessions_api.post_node_action(session_id, node_id, "stop")
        check_response_status(response, 204)

    @autotest.num("164")
    @autotest.external_id("c2222222-cccc-4ccc-cccc-cccccccccccc")
    @autotest.name("Gns3 Smoke: POST .../nodes/stop (bulk) — 204")
    async def test_c2222222_bulk_stop_204(self):
        """Bulk-остановка всех узлов возвращает 204."""
        session_dict = await self.gns3_sessions_helper.create_session()
        session_id = session_dict["session_id"]

        response = await self.gns3_sessions_api.post_bulk_node_action(session_id, "stop")
        check_response_status(response, 204)
