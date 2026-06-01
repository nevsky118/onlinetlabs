"""Smoke activity — gns3-service."""

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.api.data.gns3_service.gns3_sessions_data_api import ActivityQueryData
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_in
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestGns3SessionsActivitySmokeApi:
    """Smoke /sessions/{id}/activity — gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.gns3_sessions_api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)

    @autotest.num("165")
    @autotest.external_id("d1111111-dddd-4ddd-dddd-dddddddddddd")
    @autotest.name("Gns3 Smoke: GET .../activity — 200")
    async def test_d1111111_activity_200(self):
        """GET activity возвращает 200 и поля events/next_cursor."""
        session_dict = await self.gns3_sessions_helper.create_session()
        session_id = session_dict["session_id"]
        query = ActivityQueryData(limit=10)

        response = await self.gns3_sessions_api.get_activity(session_id, query.data)

        check_response_status(response, 200)
        body = response.json()
        assert_in("events", body, "Поле events отсутствует")
        assert_in("next_cursor", body, "Поле next_cursor отсутствует")
