"""Smoke console commands — gns3-service."""

import pytest

from autotests.api.api_helpers.gns3_service.console_helper_api import ConsoleHelper
from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.data.gns3_service.console_data_api import ConsoleCommandsQueryData
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_true


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestConsoleCommandsSmokeApi:
    """Smoke /sessions/{id}/console-commands — gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.console_helper = ConsoleHelper(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)

    @autotest.num("3561")
    @autotest.external_id("c1c3d1da-5bf9-4249-9c0f-dcb3037ba3ac")
    @autotest.name("Gns3 Smoke: GET .../console-commands — 200")
    async def test_c1c3d1da_console_commands_200(self):
        """GET console-commands returns 200 and a list body."""
        with autotest.step("Arrange: create a session and a console-commands query"):
            session_dict = await self.gns3_sessions_helper.create_session()
            session_id = session_dict["session_id"]
            query = ConsoleCommandsQueryData(limit=10)

        with autotest.step("Act: fetch console commands"):
            body = await self.console_helper.fetch_console_commands(session_id, params=query.data)

        with autotest.step("Assert: the body is a list"):
            assert_true(isinstance(body, list), "console-commands body must be a list")
