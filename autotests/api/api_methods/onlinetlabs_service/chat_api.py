# Chat API. Thin HTTP wrapper for the /chat/stream SSE endpoint.

from httpx import AsyncClient

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class ChatApi:
    """
    HTTP wrapper for the tutor chat endpoint (Vercel AI SDK v1 SSE).

    :param client: HTTP client (httpx.AsyncClient).
    :param config: ConfigModel object with the environment parameters.
    :param account_name: Account name from the configuration.
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
        POST /chat/stream. Streams the tutor response (SSE).

        :param session_id: Identifier of the active session.
        :param messages: Messages in UI Message format (role + parts).
        :return: List of SSE response lines.
        """
        with autotest.step("POST /chat/stream"):
            return await self.api_client.post_stream(
                "chat/stream",
                json_data={"id": session_id, "messages": messages},
            )
