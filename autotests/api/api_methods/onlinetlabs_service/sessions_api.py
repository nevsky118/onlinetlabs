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
