# Sessions helpers. Composition of API calls with data and checks.

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
    High-level operations on sessions.

    :param client: HTTP client used to perform the requests.
    :param config: ConfigModel object with the environment parameters.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel):
        self.client = client
        self.config = config
        self.sessions_api = SessionsApi(client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.entities_registry = EntitiesRegistry(config=config)

    async def launch_session(self, lab_slug: str) -> dict:
        """
        Launches a lab session with a check (201) and registration for cleanup.

        :param lab_slug: Lab slug.
        :return: Body of the session launch response (session_id, status, gns3_*).
        """
        with autotest.step(f"Launch the session for lab_slug={lab_slug}"):
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
        Creates a session with a check and registration for cleanup.

        :param session_data: Payload (generated when None).
        :return: Data of the created session.
        """
        if session_data is None:
            session_data = SessionCreateData().data

        with autotest.step("Create the session"):
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
        Launches a session and polls GET until status=active. Returns session_id.

        :param lab_slug: Lab slug.
        :param timeout: Timeout for waiting on the active status, in seconds.
        :return: Session identifier.
        :raises AssertionError: If the session did not move to active within the allotted time.
        """
        with autotest.step(f"Launch the session and wait for active (lab_slug={lab_slug})"):
            launched = await self.launch_session(lab_slug)
            session_id = launched["session_id"]

            loop = asyncio.get_event_loop()
            deadline = loop.time() + timeout
            while loop.time() < deadline:
                response = await self.sessions_api.get_session(session_id)
                if response.status_code == 200 and response.json().get("status") == "active":
                    return session_id
                await asyncio.sleep(0.5)

            raise AssertionError(f"Session {session_id} did not become active within {timeout}s")

    async def pick_first_node_id(self, session_id: str) -> str:
        """
        Returns the id of the first node from GET /state. Calls pytest.skip if there are no nodes.

        :param session_id: Session identifier.
        :return: Identifier of the first node.
        """
        with autotest.step(f"Get the first node_id from the session state {session_id}"):
            response = await self.sessions_api.get_session_state(session_id)
            check_response_status(response, 200)
            body = response.json()
            nodes = body.get("nodes") or []
            if not nodes:
                pytest.skip("The template project has no nodes; node tests skipped")
            return nodes[0]["id"]
