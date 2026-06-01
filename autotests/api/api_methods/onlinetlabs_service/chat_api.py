# Chat API — тонкая HTTP-обёртка для SSE-эндпоинта /chat/stream.

from httpx import AsyncClient

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class ChatApi:
    """
    HTTP-обёртка для чат-эндпоинта тьютора (Vercel AI SDK v1 SSE).

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
            controller_path="",
        )

    async def post_chat_stream(self, session_id: str, messages: list[dict]) -> list[str]:
        """
        POST /chat/stream — стрим ответа тьютора (SSE).

        :param session_id: Идентификатор активной сессии.
        :param messages: Сообщения в формате UI Message (role + parts).
        :return: Список SSE-строк ответа.
        """
        with autotest.step("POST /chat/stream"):
            return await self.api_client.post_stream(
                "chat/stream",
                json_data={"id": session_id, "messages": messages},
            )
