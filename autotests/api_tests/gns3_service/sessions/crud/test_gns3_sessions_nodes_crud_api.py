"""CRUD node actions — gns3-service."""

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestGns3SessionsNodesCrudApi:
    """CRUD /sessions/{id}/nodes/* — gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.gns3_sessions_api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)

    @autotest.num("166")
    @autotest.external_id("e1111111-eeee-4eee-eeee-eeeeeeeeeeee")
    @autotest.name("Gns3 CRUD: node action 404 при unknown session")
    async def test_e1111111_404_unknown_session(self):
        """Действие над несуществующей сессией → 404."""
        response = await self.gns3_sessions_api.post_node_action(
            "00000000-0000-0000-0000-000000000000", "node-x", "start",
        )
        check_response_status(response, 404)

    @autotest.num("167")
    @autotest.external_id("e2222222-eeee-4eee-eeee-eeeeeeeeeeee")
    @autotest.name("Gns3 CRUD: invalid action 422")
    async def test_e2222222_invalid_action_422(self):
        """Невалидное действие (destroy) → 422 от FastAPI Literal-валидации."""
        response = await self.gns3_sessions_api.post_node_action(
            "00000000-0000-0000-0000-000000000000", "node-x", "destroy",
        )
        check_response_status(response, 422)

    @autotest.num("172")
    @autotest.external_id("e3333333-eeee-4eee-eeee-eeeeeeeeeeee")
    @autotest.name("Gns3 CRUD: node action 409 при закрытой сессии")
    async def test_e3333333_409_closed_session(self):
        """Действие над закрытой (удалённой) сессией → 409."""
        with autotest.step("Создаём GNS3 сессию"):
            session_dict = await self.gns3_sessions_helper.create_session()
        session_id = session_dict["session_id"]

        with autotest.step("Закрываем сессию через DELETE"):
            delete_response = await self.gns3_sessions_api.delete_session(session_id)
            check_response_status(delete_response, 200)

        with autotest.step("Пробуем действие над узлом закрытой сессии"):
            response = await self.gns3_sessions_api.post_node_action(
                session_id, "node-x", "start",
            )
            check_response_status(response, 409)
