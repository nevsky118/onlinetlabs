# Progress API. Thin HTTP wrappers for the /users/me/progress/* endpoints.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class ProgressApi:
    """
    HTTP wrappers for the progress endpoints.

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
            controller_path="/users/me/progress",
        )

    async def get_progress(
        self,
        limit: int = 30,
        offset: int = 0,
    ) -> Response:
        """
        GET /users/me/progress. Overall user progress.

        :param limit: Max number of results.
        :param offset: Pagination offset.
        :return: HTTP response.
        """
        with autotest.step("GET /users/me/progress"):
            return await self.api_client.get("", params={
                "limit": limit,
                "offset": offset,
            })

    async def get_lab_progress(self, lab_slug: str) -> Response:
        """
        GET /users/me/progress/labs/{lab_slug}. Progress on a specific lab.

        :param lab_slug: Lab slug.
        :return: HTTP response.
        """
        with autotest.step(f"GET /users/me/progress/labs/{lab_slug}"):
            return await self.api_client.get(f"labs/{lab_slug}")

    async def post_start_lab(self, lab_slug: str) -> Response:
        """
        POST /users/me/progress/labs/{lab_slug}/start. Starts the lab.

        :param lab_slug: Lab slug.
        :return: HTTP response.
        """
        with autotest.step(f"POST /users/me/progress/labs/{lab_slug}/start"):
            return await self.api_client.post(f"labs/{lab_slug}/start")

    async def post_step_attempt(self, lab_slug: str, step_slug: str, data: dict) -> Response:
        """
        POST /users/me/progress/labs/{lab_slug}/steps/{step_slug}/attempt. Step attempt.

        :param lab_slug: Lab slug.
        :param step_slug: Step slug.
        :param data: Payload with the answer.
        :return: HTTP response.
        """
        with autotest.step(f"POST /users/me/progress/labs/{lab_slug}/steps/{step_slug}/attempt"):
            return await self.api_client.post(
                f"labs/{lab_slug}/steps/{step_slug}/attempt",
                json_data=data,
            )
