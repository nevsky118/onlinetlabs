# HTTP-обёртки для GNS3 /projects эндпоинтов.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.reports import autotest


class Gns3ProjectsApi:

    def __init__(
        self,
        client: AsyncClient = None,
        config: ConfigModel = None,
        base_url: str = "",
    ):
        self.api_client = ApiClient(
            client=client,
            config=config,
            controller_path="/projects",
            base_url=base_url,
        )

    async def post_project(self, data: dict) -> Response:
        with autotest.step("POST /projects"):
            return await self.api_client.post("", json_data=data)

    async def get_projects(self) -> Response:
        with autotest.step("GET /projects"):
            return await self.api_client.get("")

    async def delete_project(self, project_id: str) -> Response:
        with autotest.step(f"DELETE /projects/{project_id}"):
            return await self.api_client.delete(project_id)
