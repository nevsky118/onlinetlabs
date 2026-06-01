# CRUD GET /sessions/{id}/state — gns3-service.

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestGns3SessionsStateCrudApi:
    """CRUD-тесты GET /sessions/{id}/state в gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.config = config
        self.gns3_sessions_api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)

    @autotest.num("162")
    @autotest.external_id("b1111111-bbbb-4bbb-bbbb-bbbbbbbbbbbb")
    @autotest.name("Gns3 CRUD: state 404 при unknown session")
    async def test_b1111111_state_404_unknown(self):
        """Несуществующая сессия → 404."""
        # Act
        with autotest.step("Запрашиваем state для несуществующей сессии"):
            response = await self.gns3_sessions_api.get_state(
                "00000000-0000-0000-0000-000000000000"
            )

        # Assert
        with autotest.step("Проверяем статус код 404"):
            check_response_status(response, 404)
