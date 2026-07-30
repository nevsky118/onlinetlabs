# Labs API. Thin HTTP wrappers for the /labs/* endpoints.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class LabsApi:
    """
    HTTP wrappers for the labs endpoints.

    :param client: HTTP client (httpx.AsyncClient).
    :param config: ConfigModel object with the environment parameters.
    :param account_name: Account name from the configuration.
    """

    def __init__(
        self,
        client: AsyncClient = None,
        config: ConfigModel = None,
        account_name: str = ConstantsSettings.ANON_ACCOUNT,
    ):
        self.api_client = ApiClient(
            client=client,
            config=config,
            account_name=account_name,
            controller_path="/labs",
        )

    async def get_labs(
        self,
        course_slug: str | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> Response:
        """
        GET /labs. List of labs with optional filtering by course.

        :param course_slug: Filter by course slug.
        :param limit: Max number of results.
        :param offset: Pagination offset.
        :return: HTTP response.
        """
        with autotest.step("GET /labs"):
            return await self.api_client.get("", params={
                "course_slug": course_slug,
                "limit": limit,
                "offset": offset,
            })

    async def post_lab(self, data: dict) -> Response:
        with autotest.step("POST /labs"):
            return await self.api_client.post("", json_data=data)

    async def delete_lab(self, slug: str) -> Response:
        with autotest.step(f"DELETE /labs/{slug}"):
            return await self.api_client.delete(slug)

    async def get_lab_by_slug(self, slug: str) -> Response:
        """
        GET /labs/{slug}. Retrieves a lab by slug.

        :param slug: Lab slug.
        :return: HTTP response.
        """
        with autotest.step(f"GET /labs/{slug}"):
            return await self.api_client.get(slug)
