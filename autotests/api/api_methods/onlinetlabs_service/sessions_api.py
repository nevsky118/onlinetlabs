# Sessions API. Thin HTTP wrappers for the /users/me/sessions/* endpoints.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class SessionsApi:
    """
    HTTP wrappers for the sessions endpoints.

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
            controller_path="/users/me/sessions",
        )

    async def get_sessions(
        self,
        limit: int = 30,
        offset: int = 0,
    ) -> Response:
        """
        GET /users/me/sessions. List of the user's sessions.

        :param limit: Max number of results.
        :param offset: Pagination offset.
        :return: HTTP response.
        """
        with autotest.step("GET /users/me/sessions"):
            return await self.api_client.get("", params={
                "limit": limit,
                "offset": offset,
            })

    async def post_session(self, data: dict) -> Response:
        """
        POST /users/me/sessions. Creates a session.

        :param data: Payload.
        :return: HTTP response.
        """
        with autotest.step("POST /users/me/sessions"):
            return await self.api_client.post("", json_data=data)

    async def patch_session(self, session_id: str, data: dict) -> Response:
        """
        PATCH /users/me/sessions/{session_id}. Updates the session status.

        :param session_id: Session identifier.
        :param data: Payload.
        :return: HTTP response.
        """
        with autotest.step(f"PATCH /users/me/sessions/{session_id}"):
            return await self.api_client.patch(session_id, json_data=data)

    async def delete_session(self, session_id: str) -> Response:
        """
        DELETE /users/me/sessions/{session_id}. Deletes the session (for cleanup).

        :param session_id: Session identifier.
        :return: HTTP response.
        """
        with autotest.step(f"DELETE /users/me/sessions/{session_id}"):
            return await self.api_client.delete(session_id)

    async def get_credentials(self, session_id: str) -> Response:
        """
        GET /users/me/sessions/{session_id}/credentials. Retrieves the GNS3 credentials.

        :param session_id: Session identifier.
        :return: HTTP response.
        """
        with autotest.step(f"GET /users/me/sessions/{session_id}/credentials"):
            return await self.api_client.get(f"{session_id}/credentials")

    async def get_session(self, session_id: str) -> Response:
        """
        GET /users/me/sessions/{session_id}. Retrieves a session by id.

        :param session_id: Session identifier.
        :return: HTTP response.
        """
        with autotest.step(f"GET /users/me/sessions/{session_id}"):
            return await self.api_client.get(session_id)

    async def post_stop(self, session_id: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/stop. Stops the lab.

        :param session_id: Session identifier.
        :return: HTTP response.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/stop"):
            return await self.api_client.post(f"{session_id}/stop", json_data={})

    async def post_restart(self, session_id: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/restart. Restarts the lab.

        :param session_id: Session identifier.
        :return: HTTP response.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/restart"):
            return await self.api_client.post(f"{session_id}/restart", json_data={})

    async def post_reset(self, session_id: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/reset. Resets the lab.

        :param session_id: Session identifier.
        :return: HTTP response.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/reset"):
            return await self.api_client.post(f"{session_id}/reset", json_data={})

    async def post_end(self, session_id: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/end. Ends the session.

        :param session_id: Session identifier.
        :return: HTTP response.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/end"):
            return await self.api_client.post(f"{session_id}/end", json_data={})

    async def get_session_state(self, session_id: str) -> Response:
        """
        GET /users/me/sessions/{session_id}/state. Retrieves the session state.

        :param session_id: Session identifier.
        :return: HTTP response.
        """
        with autotest.step(f"GET /users/me/sessions/{session_id}/state"):
            return await self.api_client.get(f"{session_id}/state")

    async def post_node_action(self, session_id: str, node_id: str, action: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/nodes/{node_id}/{action}. Action on a node.

        :param session_id: Session identifier.
        :param node_id: Node identifier.
        :param action: Action (start/stop/suspend/reset/reload).
        :return: HTTP response.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/nodes/{node_id}/{action}"):
            return await self.api_client.post(f"{session_id}/nodes/{node_id}/{action}", json_data={})

    async def post_bulk_node_action(self, session_id: str, action: str) -> Response:
        """
        POST /users/me/sessions/{session_id}/nodes/{action}. Bulk action on nodes.

        :param session_id: Session identifier.
        :param action: Action (start/stop/suspend/reset/reload).
        :return: HTTP response.
        """
        with autotest.step(f"POST /users/me/sessions/{session_id}/nodes/{action}"):
            return await self.api_client.post(f"{session_id}/nodes/{action}", json_data={})

    async def get_session_activity(self, session_id: str, params: dict) -> Response:
        """
        GET /users/me/sessions/{session_id}/activity. Session event feed.

        :param session_id: Session identifier.
        :param params: Query parameters (limit, cursor).
        :return: HTTP response.
        """
        with autotest.step(f"GET /users/me/sessions/{session_id}/activity"):
            return await self.api_client.get(f"{session_id}/activity", params=params)
