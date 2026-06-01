# HTTP-обёртки для GNS3 sessions эндпоинтов.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.reports import autotest


class Gns3SessionsApi:
    """
    HTTP-обёртки для /sessions и /history эндпоинтов gns3-service.

    :param client: httpx.AsyncClient.
    :param config: ConfigModel.
    :param base_url: Базовый URL gns3-service.
    """

    def __init__(
        self,
        client: AsyncClient = None,
        config: ConfigModel = None,
        base_url: str = "",
    ):
        self.api_client = ApiClient(
            client=client,
            config=config,
            controller_path="/sessions",
            base_url=base_url,
        )
        self.history_client = ApiClient(
            client=client,
            config=config,
            controller_path="/history",
            base_url=base_url,
        )

    async def post_session(self, data: dict) -> Response:
        """
        POST /sessions — создание лабораторной сессии.

        :param data: Payload.
        :return: HTTP-ответ.
        """
        with autotest.step("POST /sessions"):
            return await self.api_client.post("", json_data=data)

    async def get_session(self, session_id: str) -> Response:
        """
        GET /sessions/{session_id} — статус сессии.

        :param session_id: UUID сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /sessions/{session_id}"):
            return await self.api_client.get(session_id)

    async def post_reset_password(self, session_id: str) -> Response:
        """
        POST /sessions/{session_id}/reset-password — сброс пароля.

        :param session_id: UUID сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /sessions/{session_id}/reset-password"):
            return await self.api_client.post(f"{session_id}/reset-password")

    async def delete_session(self, session_id: str) -> Response:
        """
        DELETE /sessions/{session_id} — удаление сессии.

        :param session_id: UUID сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"DELETE /sessions/{session_id}"):
            return await self.api_client.delete(session_id)

    async def get_history_actions(
        self,
        session_id: str,
        limit: int = 50,
    ) -> Response:
        """
        GET /history/{session_id}/actions — история действий сессии.

        :param session_id: UUID сессии.
        :param limit: Макс. кол-во событий.
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /history/{session_id}/actions"):
            return await self.history_client.get(
                f"{session_id}/actions",
                params={"limit": limit},
            )

    async def get_state(self, session_id: str) -> Response:
        """
        GET /sessions/{session_id}/state — снапшот состояния (nodes, links, ws_url).

        :param session_id: UUID сессии.
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /sessions/{session_id}/state"):
            return await self.api_client.get(f"{session_id}/state")

    async def post_node_action(self, session_id: str, node_id: str, action: str) -> Response:
        """
        POST /sessions/{session_id}/nodes/{node_id}/{action} — управление узлом.

        :param session_id: UUID сессии.
        :param node_id: ID узла.
        :param action: start | stop | suspend | reload.
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /sessions/{session_id}/nodes/{node_id}/{action}"):
            return await self.api_client.post(
                f"{session_id}/nodes/{node_id}/{action}",
                json_data={},
            )

    async def post_bulk_node_action(self, session_id: str, action: str) -> Response:
        """
        POST /sessions/{session_id}/nodes/{action} — массовое действие над узлами.

        :param session_id: UUID сессии.
        :param action: start | stop | suspend | reload.
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /sessions/{session_id}/nodes/{action}"):
            return await self.api_client.post(
                f"{session_id}/nodes/{action}",
                json_data={},
            )

    async def get_activity(self, session_id: str, params: dict) -> Response:
        """
        GET /sessions/{session_id}/activity — поток событий сессии.

        :param session_id: UUID сессии.
        :param params: Query-параметры (limit, cursor).
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /sessions/{session_id}/activity"):
            return await self.api_client.get(
                f"{session_id}/activity",
                params=params,
            )
