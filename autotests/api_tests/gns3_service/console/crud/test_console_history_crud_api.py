"""CRUD console commands — gns3-service."""

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.api.data.gns3_service.console_data_api import (
    ConsoleCommandsQueryData,
    UnknownNodeData,
    UnknownSessionData,
)
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_equal
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestConsoleHistoryCrudApi:
    """CRUD /sessions/{id}/console-commands — gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.gns3_sessions_api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)
        self.no_token_api = Gns3SessionsApi(
            anon_client, config, base_url=config.gns3_base_url, internal_token="",
        )

    @autotest.num("3562")
    @autotest.external_id("83458a0e-f5aa-4e1b-8c5a-293c0cbd8d57")
    @autotest.name("Gns3 CRUD: console-commands limit=0 → 422")
    async def test_83458a0e_limit_0_422(self):
        """Limit below the lower bound returns 422."""
        with autotest.step("Arrange: a session id and a limit below the lower bound"):
            session = UnknownSessionData()
            query = ConsoleCommandsQueryData(limit=0)

        with autotest.step("Act: request console-commands with limit=0"):
            response = await self.gns3_sessions_api.get_console_commands(
                session.session_id, query.data,
            )

        with autotest.step("Assert: 422"):
            check_response_status(response, 422)

    @autotest.num("3563")
    @autotest.external_id("cebb9191-d23f-4647-99e6-05df6ecf11e8")
    @autotest.name("Gns3 CRUD: console-commands limit>2000 → 422")
    async def test_cebb9191_limit_over_max_422(self):
        """Limit past the upper bound returns 422."""
        with autotest.step("Arrange: a session id and a limit past the upper bound"):
            session = UnknownSessionData()
            query = ConsoleCommandsQueryData(limit=2001)

        with autotest.step("Act: request console-commands with limit=2001"):
            response = await self.gns3_sessions_api.get_console_commands(
                session.session_id, query.data,
            )

        with autotest.step("Assert: 422"):
            check_response_status(response, 422)

    @autotest.num("3564")
    @autotest.external_id("dd76a854-b0df-4076-8c8f-1fc3773d830b")
    @autotest.name("Gns3 CRUD: console-commands filtered by node_id → empty list")
    async def test_dd76a854_node_id_filter_returns_empty_list(self):
        """node_id filter with no activity returns an empty list."""
        with autotest.step("Arrange: create a session"):
            session_dict = await self.gns3_sessions_helper.create_session()
            session_id = session_dict["session_id"]

        with autotest.step("Arrange: a node id to filter by"):
            node = UnknownNodeData()
            query = ConsoleCommandsQueryData(limit=50, node_id=node.node_id)

        with autotest.step("Act: request its console commands filtered by node_id"):
            response = await self.gns3_sessions_api.get_console_commands(session_id, query.data)

        with autotest.step("Assert: 200 with an empty list"):
            check_response_status(response, 200)
            assert_equal(response.json(), [], "console commands filtered by node_id")

    @autotest.num("3565")
    @autotest.external_id("77929e69-e702-4f65-8fc9-a629b99412c0")
    @autotest.name("Gns3 CRUD: console-commands on an unknown session → empty list, not 404")
    async def test_77929e69_unknown_session_returns_empty_list(self):
        """An unknown session id returns an empty list, not 404."""
        with autotest.step("Arrange: a session id that was never created"):
            unknown = UnknownSessionData()
            query = ConsoleCommandsQueryData(limit=50)

        with autotest.step("Act: request its console commands"):
            response = await self.gns3_sessions_api.get_console_commands(
                unknown.session_id, query.data,
            )

        with autotest.step("Assert: 200 with an empty list"):
            check_response_status(response, 200)
            assert_equal(response.json(), [], "console commands on an unknown session")

    @autotest.num("3566")
    @autotest.external_id("a612d247-d0ef-4bd9-ad90-1930e9b5ad23")
    @autotest.name("Gns3 CRUD: console-commands without the internal token → 403")
    async def test_a612d247_missing_internal_token_403(self):
        """A request with no bearer token gets 403."""
        with autotest.step("Arrange: a client that carries no internal token"):
            session = UnknownSessionData()
            query = ConsoleCommandsQueryData(limit=50)

        with autotest.step("Act: request console-commands with no Authorization header"):
            response = await self.no_token_api.get_console_commands(
                session.session_id, query.data,
            )

        with autotest.step("Assert: 403"):
            check_response_status(response, 403)
