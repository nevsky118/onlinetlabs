# Helper methods for the reconstructed console command history.

from httpx import AsyncClient

from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.api.data.gns3_service.console_data_api import ConsoleCommandsQueryData
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


class ConsoleHelper:
    """
    Helper methods for operations on the console command history.

    :param client: httpx.AsyncClient.
    :param config: ConfigModel.
    :param base_url: Base URL of gns3-service.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel, base_url: str = ""):
        self.client = client
        self.config = config
        self.gns3_sessions_api = Gns3SessionsApi(client, config, base_url=base_url)

    async def fetch_console_commands(self, session_id: str, params: dict | None = None) -> list:
        """
        Fetches /sessions/{id}/console-commands with a status check.

        :param session_id: Session UUID.
        :param params: Query parameters (generated when None).
        :return: Parsed JSON body (a list of console commands).
        """
        query = params if params is not None else ConsoleCommandsQueryData().data

        with autotest.step(f"Fetch console commands for session {session_id}"):
            response = await self.gns3_sessions_api.get_console_commands(session_id, query)

        check_response_status(response, 200)

        return response.json()
