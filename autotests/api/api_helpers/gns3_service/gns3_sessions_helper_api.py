# Helper methods for GNS3 sessions.

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
    Helper methods for operations on GNS3 sessions.

    :param client: httpx.AsyncClient.
    :param config: ConfigModel.
    :param base_url: Base URL of gns3-service.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel, base_url: str = ""):
        self.client = client
        self.config = config
        self.gns3_sessions_api = Gns3SessionsApi(client, config, base_url=base_url)
        self.entities_registry = EntitiesRegistry(config=config)

    async def create_session(self, session_data: dict | None = None) -> dict:
        """
        Creates a GNS3 session with a check and registration for cleanup.

        :param session_data: Payload (generated when None).
        :return: Data of the created session.
        """
        if session_data is None:
            session_data = Gns3SessionCreateData(
                lab_template_project_id=self.config.gns3_lab_template_project_id or None,
            ).data

        with autotest.step("Create the GNS3 session"):
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
        Fetches /sessions/{id}/state and checks for 200.

        :param session_id: Session UUID.
        :return: JSON snapshot of the state.
        """
        with autotest.step("Get the session state"):
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
        Waits until the node moves to the expected status.

        :param session_id: Session UUID.
        :param node_id: Node ID.
        :param expected: Expected status (started, stopped, suspended, ...).
        :param timeout: Wait timeout in seconds.
        :raises AssertionError: If the status is not reached within timeout.
        """
        import asyncio

        with autotest.step(f"Wait for node {node_id} to reach status {expected}"):
            deadline = asyncio.get_event_loop().time() + timeout
            last_status = None
            while asyncio.get_event_loop().time() < deadline:
                state = await self.get_state_and_verify(session_id)
                node = next((row for row in state["nodes"] if row["id"] == node_id), None)
                last_status = node["status"] if node else "missing"
                if last_status == expected:
                    return
                await asyncio.sleep(0.5)
            raise AssertionError(
                f"Node {node_id} not in {expected} within {timeout}s (last: {last_status})"
            )

    async def pick_first_node_id(self, session_id: str) -> str:
        """
        Returns the ID of the session's first node, or skips if there are no nodes.

        :param session_id: Session UUID.
        :return: ID of the first node.
        """
        import pytest

        state = await self.get_state_and_verify(session_id)
        if not state["nodes"]:
            pytest.skip("The autotest-lab template project has no nodes; add nodes to run the node tests")
        return state["nodes"][0]["id"]
