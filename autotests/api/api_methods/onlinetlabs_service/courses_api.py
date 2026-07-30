# Courses API. Thin HTTP wrappers for the /courses/* endpoints.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class CoursesApi:
    """
    HTTP wrappers for the courses endpoints.

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
            controller_path="/courses",
        )

    async def get_courses(
        self,
        limit: int = 30,
        offset: int = 0,
    ) -> Response:
        """
        GET /courses. List of courses.

        :param limit: Max number of results.
        :param offset: Pagination offset.
        :return: HTTP response.
        """
        with autotest.step("GET /courses"):
            return await self.api_client.get("", params={
                "limit": limit,
                "offset": offset,
            })

    async def get_course_by_slug(self, slug: str) -> Response:
        """
        GET /courses/{slug}. Retrieves a course by slug.

        :param slug: Course slug.
        :return: HTTP response.
        """
        with autotest.step(f"GET /courses/{slug}"):
            return await self.api_client.get(slug)
