# Progress helpers. Composition of API calls with data and checks.

from httpx import AsyncClient

from autotests.api.api_methods.onlinetlabs_service.progress_api import ProgressApi
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


class ProgressHelperApi:
    """
    High-level operations on progress.

    :param client: HTTP client used to perform the requests.
    :param config: ConfigModel object with the environment parameters.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel):
        self.client = client
        self.config = config
        self.progress_api = ProgressApi(client, config, ConstantsSettings.REGISTERED_ACCOUNT)

    async def start_lab(self, lab_slug: str) -> dict:
        """
        Starts a lab with a check.

        :param lab_slug: Lab slug.
        :return: Progress data.
        """
        with autotest.step("Start the lab"):
            response = await self.progress_api.post_start_lab(lab_slug=lab_slug)

        check_response_status(response, 201)
        return response.json()
