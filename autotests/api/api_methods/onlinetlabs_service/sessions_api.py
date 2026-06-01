# Sessions API — тонкие HTTP-обёртки для /users/me/sessions/* эндпоинтов.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class SessionsApi:
    """
    HTTP-обёртки для sessions-эндпоинтов.

    :param client: HTTP-клиент (httpx.AsyncClient).
    :param config: Объект ConfigModel с параметрами окружения.
    :param account_name: Название учётной записи из конфигурации.
    """

    def __init__(
        self,
        client: AsyncClient = None,
        config: ConfigModel = None,
        account_name: str = ConstantsSettings.REGISTERED_ACCOUNT,
    ):
        self.api_client = ApiClient(
            client=client,
            config=config,
            account_name=account_name,
            controller_path="/users/me/sessions",
        )

    async def get_sessions(
        self,
        limit: int = 30,
        offset: int = 0,
    ) -> Response:
        """
        GET /users/me/sessions — список сессий пользователя.

        :param limit: Макс. количество результатов.
        :param offset: Смещение для пагинации.
        :return: HTTP-ответ.
        """
        with autotest.step("GET /users/me/sessions"):
            return await self.api_client.get("", params={
                "limit": limit,
                "offset": offset,
            })

    async def post_session(self, data: dict) -> Response:
        """
        POST /users/me/sessions — создание сессии.

        :param data: Payload.
        :return: HTTP-ответ.
        """
        with autotest.step("POST /users/me/sessions"):
            return await self.api_client.post("", json_data=data)

    async def patch_session(self, session_id: str, data: dict) -> Response:
        """
        PATCH /users/me/sessions/{session_id} — обновление статуса сессии.

        :param session_id: Идентификатор сессии.
        :param data: Payload.
        :return: HTTP-ответ.
        """
        with autotest.step(f"PATCH /users/me/sessions/{session_id}"):
            return await self.api_client.patch(session_id, json_data=data)

    async def delete_session(self, session_id: str) -> Response:
        """
        DELETE /users/me/sessions/{session_id} — удаление сессии (для очистки).

        :param session_id: Идентификатор сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"DELETE /users/me/sessions/{session_id}"):
            return await self.api_client.delete(session_id)

    async def get_credentials(self, session_id: str) -> Response:
        """
        GET /users/me/sessions/{session_id}/credentials — получение учётных данных GNS3.

        :param session_id: Идентификатор сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /users/me/sessions/{session_id}/credentials"):
            return await self.api_client.get(f"{session_id}/credentials")

    async def get_session(self, session_id: str) -> Response:
        """
        GET /users/me/sessions/{session_id} — получение сессии по id.

        :param session_id: Идентификатор сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /users/me/sessions/{session_id}"):
            return await self.api_client.get(session_id)

    async def post_stop(self, session_id: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/stop — остановка лаборатории.

        :param session_id: Идентификатор сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/stop"):
            return await self.api_client.post(f"{session_id}/stop", json_data={})

    async def post_restart(self, session_id: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/restart — перезапуск лаборатории.

        :param session_id: Идентификатор сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/restart"):
            return await self.api_client.post(f"{session_id}/restart", json_data={})

    async def post_reset(self, session_id: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/reset — сброс лаборатории.

        :param session_id: Идентификатор сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/reset"):
            return await self.api_client.post(f"{session_id}/reset", json_data={})

    async def post_end(self, session_id: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/end — завершение сессии.

        :param session_id: Идентификатор сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/end"):
            return await self.api_client.post(f"{session_id}/end", json_data={})

    async def get_session_state(self, session_id: str) -> Response:
        """
        GET /users/me/sessions/{session_id}/state — получение состояния сессии.

        :param session_id: Идентификатор сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /users/me/sessions/{session_id}/state"):
            return await self.api_client.get(f"{session_id}/state")

    async def post_node_action(self, session_id: str, node_id: str, action: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/nodes/{node_id}/{action} — действие над узлом.

        :param session_id: Идентификатор сессии.
        :param node_id: Идентификатор узла.
        :param action: Действие (start/stop/suspend/reset/reload).
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/nodes/{node_id}/{action}"):
            return await self.api_client.post(f"{session_id}/nodes/{node_id}/{action}", json_data={})

    async def post_bulk_node_action(self, session_id: str, action: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/nodes/{action} — bulk-действие над узлами.

        :param session_id: Идентификатор сессии.
        :param action: Действие (start/stop/suspend/reset/reload).
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/nodes/{action}"):
            return await self.api_client.post(f"{session_id}/nodes/{action}", json_data={})

    async def get_session_activity(self, session_id: str, params: dict) -> Response:
        """
        GET /users/me/sessions/{session_id}/activity — лента событий сессии.

        :param session_id: Идентификатор сессии.
        :param params: Query-параметры (limit, cursor).
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /users/me/sessions/{session_id}/activity"):
            return await self.api_client.get(f"{session_id}/activity", params=params)
