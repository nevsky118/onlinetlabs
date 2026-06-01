# Вспомогательные методы для GNS3 sessions.

from httpx import AsyncClient

from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.api.data.gns3_service.gns3_sessions_data_api import Gns3SessionCreateData
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.delete_entities.entities_registry import EntitiesRegistry
from autotests.settings.delete_entities.entity_types import EntitiesTypes
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


class Gns3SessionsHelperApi:
    """
    Вспомогательные методы для операций с GNS3 сессиями.

    :param client: httpx.AsyncClient.
    :param config: ConfigModel.
    :param base_url: Базовый URL gns3-service.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel, base_url: str = ""):
        self.client = client
        self.config = config
        self.gns3_sessions_api = Gns3SessionsApi(client, config, base_url=base_url)
        self.entities_registry = EntitiesRegistry(config=config)

    async def create_session(self, session_data: dict | None = None) -> dict:
        """
        Создание GNS3 сессии с проверкой и регистрацией для очистки.

        :param session_data: Payload (если None — генерируется).
        :return: Данные созданной сессии.
        """
        if session_data is None:
            session_data = Gns3SessionCreateData(
                lab_template_project_id=self.config.gns3_lab_template_project_id or None,
            ).data

        with autotest.step("Создаём GNS3 сессию"):
            response = await self.gns3_sessions_api.post_session(data=session_data)

        check_response_status(response, 201)

        result = response.json()

        self.entities_registry.add_id(
            ent_type=EntitiesTypes.gns3_session,
            ent_param=result.get("session_id"),
        )

        return result

    async def get_state_and_verify(self, session_id: str) -> dict:
        """
        Получает /sessions/{id}/state и проверяет 200.

        :param session_id: UUID сессии.
        :return: JSON-снапшот состояния.
        """
        with autotest.step("Получить состояние сессии"):
            response = await self.gns3_sessions_api.get_state(session_id)
            check_response_status(response, 200)
            return response.json()

    async def wait_node_status(
        self,
        session_id: str,
        node_id: str,
        expected: str,
        timeout: float = 15.0,
    ) -> None:
        """
        Ждёт, пока узел не перейдёт в ожидаемый статус.

        :param session_id: UUID сессии.
        :param node_id: ID узла.
        :param expected: Ожидаемый статус (started, stopped, suspended, ...).
        :param timeout: Тайм-аут ожидания (сек).
        :raises AssertionError: Если статус не достигнут за timeout.
        """
        import asyncio

        with autotest.step(f"Ждём node {node_id} в статусе {expected}"):
            deadline = asyncio.get_event_loop().time() + timeout
            last_status = None
            while asyncio.get_event_loop().time() < deadline:
                state = await self.get_state_and_verify(session_id)
                node = next((n for n in state["nodes"] if n["id"] == node_id), None)
                last_status = node["status"] if node else "missing"
                if last_status == expected:
                    return
                await asyncio.sleep(0.5)
            raise AssertionError(
                f"Node {node_id} not in {expected} within {timeout}s (last: {last_status})"
            )

    async def pick_first_node_id(self, session_id: str) -> str:
        """
        Возвращает ID первого узла сессии или skip, если узлов нет.

        :param session_id: UUID сессии.
        :return: ID первого узла.
        """
        import pytest

        state = await self.get_state_and_verify(session_id)
        if not state["nodes"]:
            pytest.skip("Шаблонный проект autotest-lab без узлов; добавь узлы для node-тестов")
        return state["nodes"][0]["id"]
