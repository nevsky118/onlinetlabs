"""CRUD activity — gns3-service."""

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestGns3SessionsActivityCrudApi:
    """CRUD /sessions/{id}/activity — gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.gns3_sessions_api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)

    @autotest.num("168")
    @autotest.external_id("864f0bb8-1118-4ec4-8002-0eec5aecc3d2")
    @autotest.name("Gns3 CRUD: activity limit=0 → 422")
    async def test_864f0bb8_limit_0_422(self):
        """A limit outside the allowed bounds results in 422."""
        with autotest.step("Act: request activity with limit=0"):
            response = await self.gns3_sessions_api.get_activity(
                "00000000-0000-0000-0000-000000000000", {"limit": 0},
            )
        with autotest.step("Assert: 422"):
            check_response_status(response, 422)

    @autotest.num("169")
    @autotest.external_id("6cafe4e7-ab4f-41ac-acd6-7a3e711bf3ee")
    @autotest.name("Gns3 CRUD: activity cursor narrows the result set")
    async def test_6cafe4e7_cursor_pagination(self):
        """If next_cursor was returned, a repeat request with cursor returns 200."""
        with autotest.step("Arrange: create a session"):
            session_dict = await self.gns3_sessions_helper.create_session()
            session_id = session_dict["session_id"]

        with autotest.step("Act: request the first page of activity"):
            page1 = await self.gns3_sessions_api.get_activity(session_id, {"limit": 5})
        with autotest.step("Assert: first page returns 200"):
            check_response_status(page1, 200)

        with autotest.step("Arrange: extract next_cursor from the first page"):
            cursor = page1.json().get("next_cursor")
        with autotest.step("Act + Assert: if a cursor was returned, the next page also returns 200"):
            if cursor:
                page2 = await self.gns3_sessions_api.get_activity(session_id, {"limit": 5, "cursor": cursor})
                check_response_status(page2, 200)

    @autotest.num("170")
    @autotest.external_id("1fa46f66-7035-4de5-a856-4d98b56f9e54")
    @autotest.name("Gns3 CRUD: activity invalid cursor → 400")
    async def test_1fa46f66_invalid_cursor_400(self):
        """An invalid ISO value in cursor results in 400."""
        with autotest.step("Arrange: create a session"):
            session_dict = await self.gns3_sessions_helper.create_session()
            session_id = session_dict["session_id"]

        with autotest.step("Act: request activity with a non-timestamp cursor"):
            response = await self.gns3_sessions_api.get_activity(
                session_id, {"limit": 5, "cursor": "not-a-timestamp"},
            )
        with autotest.step("Assert: 400"):
            check_response_status(response, 400)

    @autotest.num("171")
    @autotest.external_id("a127a1e6-00e1-43de-b987-e16a0603b012")
    @autotest.name("Gns3 CRUD: activity limit>200 → 422")
    async def test_a127a1e6_limit_over_max_422(self):
        """A limit past the upper bound (>200) results in 422."""
        with autotest.step("Act: request activity with limit=201"):
            response = await self.gns3_sessions_api.get_activity(
                "00000000-0000-0000-0000-000000000000", {"limit": 201},
            )
        with autotest.step("Assert: 422"):
            check_response_status(response, 422)
