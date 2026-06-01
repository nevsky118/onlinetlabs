"""e2e: WS /sessions/{id}/events на gns3-service."""

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.settings.api_client.ws_client import WSClient
from autotests.settings.reports import autotest


@pytest.mark.e2e
@pytest.mark.asyncio
class TestGns3SessionWsE2E:
    """e2e WS /sessions/{id}/events — gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_base = config.gns3_base_url

    @autotest.num("90")
    @autotest.external_id("aa111111-eeee-4eee-eeee-eeeeeeeeeeee")
    @autotest.name("Gns3 e2e: WS connects + receives snapshot")
    async def test_aa111111_ws_snapshot(self):
        """Подключение к WS возвращает snapshot первым сообщением."""
        session_dict = await self.helper.create_session()
        session_id = session_dict["session_id"]

        ws_client = WSClient(self.gns3_base)
        async with await ws_client.connect(f"/sessions/{session_id}/events") as ws:
            msg = await ws_client.recv_json(ws, timeout=15)
            assert msg["type"] == "snapshot", f"Expected snapshot, got {msg['type']}"
            assert msg["payload"]["session_id"] == session_id
