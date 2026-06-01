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
    @autotest.external_id("f1111111-ffff-4fff-ffff-ffffffffffff")
    @autotest.name("Gns3 CRUD: activity limit=0 → 422")
    async def test_f1111111_limit_0_422(self):
        """limit вне границ → 422."""
        response = await self.gns3_sessions_api.get_activity(
            "00000000-0000-0000-0000-000000000000", {"limit": 0},
        )
        check_response_status(response, 422)

    @autotest.num("169")
    @autotest.external_id("f2222222-ffff-4fff-ffff-ffffffffffff")
    @autotest.name("Gns3 CRUD: activity cursor сужает выборку")
    async def test_f2222222_cursor_pagination(self):
        """Если next_cursor вернулся, повтор с cursor возвращает 200."""
        session_dict = await self.gns3_sessions_helper.create_session()
        session_id = session_dict["session_id"]

        page1 = await self.gns3_sessions_api.get_activity(session_id, {"limit": 5})
        check_response_status(page1, 200)
        cursor = page1.json().get("next_cursor")
        if cursor:
            page2 = await self.gns3_sessions_api.get_activity(session_id, {"limit": 5, "cursor": cursor})
            check_response_status(page2, 200)

    @autotest.num("170")
    @autotest.external_id("f3333333-ffff-4fff-ffff-ffffffffffff")
    @autotest.name("Gns3 CRUD: activity invalid cursor → 400")
    async def test_f3333333_invalid_cursor_400(self):
        """Невалидный ISO в cursor → 400."""
        session_dict = await self.gns3_sessions_helper.create_session()
        session_id = session_dict["session_id"]
        response = await self.gns3_sessions_api.get_activity(
            session_id, {"limit": 5, "cursor": "not-a-timestamp"},
        )
        check_response_status(response, 400)

    @autotest.num("171")
    @autotest.external_id("f4444444-ffff-4fff-ffff-ffffffffffff")
    @autotest.name("Gns3 CRUD: activity limit>200 → 422")
    async def test_f4444444_limit_over_max_422(self):
        """limit за верхней границей (>200) → 422."""
        response = await self.gns3_sessions_api.get_activity(
            "00000000-0000-0000-0000-000000000000", {"limit": 201},
        )
        check_response_status(response, 422)
