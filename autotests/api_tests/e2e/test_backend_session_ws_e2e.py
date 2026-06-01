"""e2e: WS /users/me/sessions/ws/{id}/events на backend."""

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.settings.api_client.ws_client import WSClient
from autotests.settings.reports import autotest


@pytest.mark.e2e
@pytest.mark.asyncio
class TestBackendSessionWsE2E:
    """e2e WS /users/me/sessions/ws/{id}/events."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config, registered_account):
        self.sessions_helper = SessionsHelperApi(anon_client, config)
        self.config = config
        self.token = registered_account.token

    @autotest.num("91")
    @autotest.external_id("91111111-9999-4999-9999-999999999999")
    @autotest.name("Backend e2e: WS connects + receives snapshot")
    async def test_91111111_ws_snapshot(self):
        """Подключение к WS возвращает snapshot первым сообщением."""
        session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")
        ws_client = WSClient(self.config.base_url, token=self.token)
        async with await ws_client.connect(f"/users/me/sessions/ws/{session_id}/events") as ws:
            msg = await ws_client.recv_json(ws, timeout=15)
            assert msg["type"] == "snapshot", f"Expected snapshot, got {msg.get('type')}"

    @autotest.num("92")
    @autotest.external_id("92111111-9999-4999-9999-999999999999")
    @autotest.name("Backend e2e: WS закрывается 4401 без токена")
    async def test_92111111_unauthorized_4401(self):
        """Подключение без токена → close 4401."""
        ws_client = WSClient(self.config.base_url)  # no token
        with pytest.raises(Exception) as exc_info:
            async with await ws_client.connect(
                "/users/me/sessions/ws/00000000-0000-0000-0000-000000000000/events"
            ) as ws:
                await ws.recv()
        err = str(exc_info.value).lower()
        assert any(s in err for s in ("4401", "unauthorized", "forbidden", "rejected")), (
            f"Expected 4401/Unauthorized in error, got {exc_info.value}"
        )
