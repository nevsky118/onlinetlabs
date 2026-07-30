# Helper for the e2e tests of the GNS3 → MCP → Agent pipeline.

import os
import sys
import uuid

import httpx

from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.delete_entities.entities_registry import EntitiesRegistry
from autotests.settings.delete_entities.entity_types import EntitiesTypes
from autotests.settings.reports import autotest

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "backend")
    ),
)


class GNS3MCPHelper:
    """
    Manages the GNS3 project and the MCP client for the e2e tests.

    :param config: ConfigModel.
    """

    def __init__(self, config: ConfigModel):
        self.config = config
        self.gns3_url = config.gns3_url
        self.mcp_url = config.gns3_mcp_url
        self._jwt: str | None = None
        self._project_id: str | None = None
        self.entities_registry = EntitiesRegistry(config=config)

    async def authenticate(self) -> str:
        """Obtain a JWT from the GNS3 server."""
        with autotest.step("Аутентификация в GNS3"):
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gns3_url}/v3/access/users/authenticate",
                    json={
                        "username": self.config.gns3_admin_user,
                        "password": self.config.gns3_admin_password,
                    },
                )
                self._jwt = response.json()["access_token"]
                return self._jwt

    async def create_project(self, name: str) -> str:
        """Create a GNS3 project with a unique name and register it for cleanup."""
        unique_name = f"{name}-{uuid.uuid4().hex[:8]}"
        with autotest.step(f"Создание GNS3 проекта '{unique_name}'"):
            async with httpx.AsyncClient(
                base_url=self.gns3_url,
                headers={"Authorization": f"Bearer {self._jwt}"},
            ) as client:
                response = await client.post("/v3/projects", json={"name": unique_name})
                self._project_id = response.json()["project_id"]

                self.entities_registry.add_id(
                    ent_type=EntitiesTypes.gns3_project,
                    ent_param=self._project_id,
                )

                return self._project_id

    async def create_vpcs_nodes(self, names: list[str]) -> list[dict]:
        """Create VPCS nodes in the project."""
        with autotest.step(f"Создание VPCS нод: {names}"):
            async with httpx.AsyncClient(
                base_url=self.gns3_url,
                headers={"Authorization": f"Bearer {self._jwt}"},
            ) as client:
                templates_response = await client.get("/v3/templates")
                vpcs_id = None
                for template in templates_response.json():
                    if template["name"] == "VPCS":
                        vpcs_id = template["template_id"]
                        break

                nodes = []
                for i, name in enumerate(names):
                    response = await client.post(
                        f"/v3/projects/{self._project_id}/templates/{vpcs_id}",
                        json={"x": i * 200, "y": 0},
                    )
                    node = response.json()
                    await client.put(
                        f"/v3/projects/{self._project_id}/nodes/{node['node_id']}",
                        json={"name": name},
                    )
                    nodes.append(node)
                return nodes

    def get_mcp_client(self):
        """Create an MCPClient for the MCP server."""
        from mcp_client.client import MCPClient
        return MCPClient(self.mcp_url)

    def get_session_context(self):
        """Create a SessionContext for MCP calls."""
        from mcp_sdk.context import SessionContext
        return SessionContext(
            user_id="e2e-test-user",
            session_id="e2e-test-session",
            environment_url="http://gns3-server:3080",
            project_id=self._project_id,
            metadata={"gns3_jwt": self._jwt},
        )
