# Sessions хелперы — композиция API-вызовов с данными и проверками.

import asyncio

import pytest
from httpx import AsyncClient

from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.api.data.onlinetlabs_service.sessions_data_api import SessionCreateData
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.delete_entities.entities_registry import EntitiesRegistry
from autotests.settings.delete_entities.entity_types import EntitiesTypes
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


class SessionsHelperApi:
    """
    Высокоуровневые операции с сессиями.

    :param client: HTTP-клиент для выполнения запросов.
    :param config: Объект ConfigModel с параметрами окружения.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel):
        self.client = client
        self.config = config
        self.sessions_api = SessionsApi(client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.entities_registry = EntitiesRegistry(config=config)

    async def launch_session(self, lab_slug: str) -> dict:
        """
        Запуск лабораторной сессии с проверкой (201) и регистрацией для очистки.

        :param lab_slug: Slug лабораторной работы.
        :return: Тело ответа запуска сессии (session_id, status, gns3_*).
        """
        with autotest.step(f"Запускаем сессию для lab_slug={lab_slug}"):
            response = await self.sessions_api.post_session(data={"lab_slug": lab_slug})

        check_response_status(response, 201)

        result = response.json()

        self.entities_registry.add_id(
            ent_type=EntitiesTypes.learning_session,
            ent_param=result.get("session_id"),
        )

        return result

    async def create_session(self, session_data: dict | None = None) -> dict:
        """
        Создание сессии с проверкой и регистрацией для очистки.

        :param session_data: Payload (если None — генерируется).
        :return: Данные созданной сессии.
        """
        if session_data is None:
            session_data = SessionCreateData().data

        with autotest.step("Создаём сессию"):
            response = await self.sessions_api.post_session(data=session_data)

        check_response_status(response, 201)

        result = response.json()

        self.entities_registry.add_id(
            ent_type=EntitiesTypes.session,
            ent_param=result.get("id"),
        )

        return result

    async def launch_and_wait_active(
        self,
        lab_slug: str = "autotest-lab",
        timeout: float = 30.0,
    ) -> str:
        """
        Запускает сессию и поллит GET до status=active. Возвращает session_id.

        :param lab_slug: Slug лабораторной работы.
        :param timeout: Таймаут ожидания active-статуса, секунды.
        :return: Идентификатор сессии.
        :raises AssertionError: Если сессия не перешла в active за отведённое время.
        """
        with autotest.step(f"Запускаем сессию и ждём active (lab_slug={lab_slug})"):
            launched = await self.launch_session(lab_slug)
            session_id = launched["session_id"]

            loop = asyncio.get_event_loop()
            deadline = loop.time() + timeout
            while loop.time() < deadline:
                response = await self.sessions_api.get_session(session_id)
                if response.status_code == 200 and response.json().get("status") == "active":
                    return session_id
                await asyncio.sleep(0.5)

            raise AssertionError(f"Session {session_id} не перешла в active за {timeout}s")

    async def pick_first_node_id(self, session_id: str) -> str:
        """
        Возвращает id первого узла из GET /state. Если узлов нет — pytest.skip.

        :param session_id: Идентификатор сессии.
        :return: Идентификатор первого узла.
        """
        with autotest.step(f"Получаем первый node_id из state сессии {session_id}"):
            response = await self.sessions_api.get_session_state(session_id)
            check_response_status(response, 200)
            body = response.json()
            nodes = body.get("nodes") or []
            if not nodes:
                pytest.skip("Шаблонный проект без узлов; node-тесты пропущены")
            return nodes[0]["id"]
