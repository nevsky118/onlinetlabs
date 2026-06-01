# Smoke-тесты POST node actions через backend.

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
    """Smoke-тесты /users/me/sessions/{id}/nodes/*."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("71")
    @autotest.external_id("71111111-7777-4777-7777-777777777777")
    @autotest.name("Sessions Smoke: POST .../nodes/{id}/stop — 200")
    async def test_71111111_node_stop_200(self):
        """POST per-node stop возвращает 200."""
        # Arrange
        session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")
        node_id = await self.sessions_helper.pick_first_node_id(session_id)

        # Act
        with autotest.step(f"POST .../sessions/{session_id}/nodes/{node_id}/stop"):
            response = await self.sessions_api.post_node_action(session_id, node_id, "stop")

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

    @autotest.num("72")
    @autotest.external_id("72111111-7777-4777-7777-777777777777")
    @autotest.name("Sessions Smoke: POST .../nodes/stop (bulk) — 200")
    async def test_72111111_bulk_stop_200(self):
        """POST bulk stop возвращает 200."""
        # Arrange
        session_id = await self.sessions_helper.launch_and_wait_active("autotest-lab")

        # Act
        with autotest.step(f"POST .../sessions/{session_id}/nodes/stop"):
            response = await self.sessions_api.post_bulk_node_action(session_id, "stop")

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)
