# Smoke-тесты GET /sessions/{id}/state в gns3-service.

import pytest

from autotests.api.api_helpers.gns3_service.gns3_sessions_helper_api import Gns3SessionsHelperApi
from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_in, assert_is_not_none
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestGns3SessionsStateSmokeApi:
    """Smoke-тесты GET /sessions/{id}/state в gns3-service."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.config = config
        self.gns3_sessions_api = Gns3SessionsApi(anon_client, config, base_url=config.gns3_base_url)
        self.gns3_sessions_helper = Gns3SessionsHelperApi(anon_client, config, base_url=config.gns3_base_url)

    @autotest.num("160")
    @autotest.external_id("a1111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa")
    @autotest.name("Gns3 Smoke: GET /sessions/{id}/state — 200")
    async def test_a1111111_state_200(self):
        """GET /sessions/{id}/state возвращает 200 для активной сессии."""
        # Arrange
        with autotest.step("Создаём GNS3 сессию"):
            session_dict = await self.gns3_sessions_helper.create_session()
        session_id = session_dict["session_id"]

        # Act
        with autotest.step("Запрашиваем состояние сессии"):
            response = await self.gns3_sessions_api.get_state(session_id)

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

    @autotest.num("161")
    @autotest.external_id("a2222222-aaaa-4aaa-aaaa-aaaaaaaaaaaa")
    @autotest.name("Gns3 Smoke: state содержит nodes/links/metrics")
    async def test_a2222222_state_shape(self):
        """state-ответ содержит поля nodes, links, metrics."""
        # Arrange
        with autotest.step("Создаём GNS3 сессию"):
            session_dict = await self.gns3_sessions_helper.create_session()
        session_id = session_dict["session_id"]

        # Act
        with autotest.step("Получаем состояние сессии"):
            body = await self.gns3_sessions_helper.get_state_and_verify(session_id)

        # Assert
        with autotest.step("Проверяем структуру ответа"):
            assert_is_not_none(body.get("session_id"), "session_id отсутствует")
            assert_in("nodes", body, "поле nodes отсутствует")
            assert_in("links", body, "поле links отсутствует")
            assert_in("metrics", body, "поле metrics отсутствует")
            assert_in("nodes_total", body["metrics"], "metrics.nodes_total отсутствует")
