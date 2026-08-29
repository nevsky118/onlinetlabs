"""e2e: WS /users/me/sessions/ws/{id}/events on the backend."""

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.settings.api_client.ws_client import WSClient
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_equal, assert_true


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
    @autotest.external_id("7948fa28-b833-44e2-b8ee-9cafb8d558d3")
    @autotest.name("Backend e2e: WS connects + receives snapshot")
    async def test_7948fa28_ws_snapshot(self):
        """Connecting to the WS returns a snapshot as the first message."""
        with autotest.step("Arrange: launch an active session and a WS client with a token"):
            session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")
            ws_client = WSClient(self.config.base_url, token=self.token)

        with autotest.step("Act + Assert: connect and check the first message is a snapshot"):
            async with await ws_client.connect(f"/users/me/sessions/ws/{session_id}/events") as ws:
                msg = await ws_client.recv_json(ws, timeout=15)
                assert_equal(msg["type"], "snapshot", "type")

    @autotest.num("92")
    @autotest.external_id("99b8112b-e7aa-4899-a20e-c9a5adffbea1")
    @autotest.name("Backend e2e: WS closes 4401 without a token")
    async def test_99b8112b_unauthorized_4401(self):
        """Connecting without a token results in close 4401."""
        with autotest.step("Arrange: WS client with no token"):
            ws_client = WSClient(self.config.base_url)  # no token

        with autotest.step("Act: connect without a token"):
            with pytest.raises(Exception) as exc_info:
                async with await ws_client.connect(
                    "/users/me/sessions/ws/00000000-0000-0000-0000-000000000000/events"
                ) as ws:
                    await ws.recv()

        with autotest.step("Assert: close reason is 4401/unauthorized"):
            err = str(exc_info.value).lower()
            assert_true(
                any(marker in err for marker in ("4401", "unauthorized", "forbidden", "rejected")),
                "close reason names the rejection",
            )
