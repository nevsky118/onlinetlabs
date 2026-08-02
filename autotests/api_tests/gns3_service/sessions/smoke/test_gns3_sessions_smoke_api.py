# Smoke tests for GNS3 /sessions and /history.

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.api.data.gns3_service.gns3_sessions_data_api import Gns3SessionCreateData
from autotests.settings.delete_entities.entities_cleanup import delete_test_entities
from autotests.settings.delete_entities.entity_types import EntitiesTypes
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_is_not_none
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestGns3SessionsSmokeApi:
    """Smoke tests for GNS3 /sessions."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.config = config
        self.gns3_sessions_api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)

    @autotest.num("101")
    @autotest.external_id("5fa35cd6-e3d3-4ed7-b586-a7cd16a31e04")
    @autotest.name("Smoke: POST /sessions — 201 создание GNS3 сессии")
    async def test_5fa35cd6_create_gns3_session(self):
        """Creating a GNS3 session returns 201."""
        # Arrange
        session_data = Gns3SessionCreateData(
            lab_template_project_id=self.config.gns3_lab_template_project_id or None,
        )

        # Act
        with autotest.step("Создаём GNS3 сессию"):
            response = await self.gns3_sessions_api.post_session(data=session_data.data)

        # Assert
        with autotest.step("Проверяем статус код 201"):
            check_response_status(response, 201)

        with autotest.step("Проверяем наличие session_id в ответе"):
            body = response.json()
            assert_is_not_none(body.get("session_id"), "session_id не должен быть None")
            delete_test_entities.entities_registry._config = self.config
            delete_test_entities.entities_registry.add_id(
                ent_type=EntitiesTypes.gns3_session,
                ent_param=body["session_id"],
            )

    @autotest.num("104")
    @autotest.external_id("43bece25-725e-4c93-9efb-a0b77342bd40")
    @autotest.name("Smoke: DELETE /sessions/{session_id} — 200 удаление сессии")
    async def test_43bece25_delete_gns3_session(self):
        """Deleting a GNS3 session returns 200."""
        # Arrange
        with autotest.step("Создаём GNS3 сессию"):
            session = await self.gns3_sessions_helper.create_session()

        # Act
        with autotest.step("Удаляем сессию"):
            response = await self.gns3_sessions_api.delete_session(session["session_id"])

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

    @autotest.num("105")
    @autotest.external_id("0463e32e-ceb5-49ee-9f0b-7500189c0940")
    @autotest.name("Smoke: GET /history/{session_id}/actions — 200 история действий")
    async def test_0463e32e_get_gns3_history(self):
        """Fetching the action history of a GNS3 session returns 200."""
        # Arrange
        with autotest.step("Создаём GNS3 сессию"):
            session = await self.gns3_sessions_helper.create_session()

        # Act
        with autotest.step("Запрашиваем историю действий"):
            response = await self.gns3_sessions_api.get_history_actions(session["session_id"])

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)
