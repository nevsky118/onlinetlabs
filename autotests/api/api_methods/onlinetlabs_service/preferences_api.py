# Preferences API. Thin HTTP wrappers for /users/me/preferences.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class PreferencesApi:
    """
    HTTP wrappers for the preferences endpoints.

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
            controller_path="/users/me/preferences",
        )

    async def get_preferences(self) -> Response:
        """
        GET /users/me/preferences. Settings of the current user.

        :return: HTTP response.
        """
        with autotest.step("GET /users/me/preferences"):
            return await self.api_client.get("")

    async def patch_preferences(self, data: dict) -> Response:
        """
        PATCH /users/me/preferences. Updates the user settings.

        :param data: Payload with the settings (for example, default_model_id).
        :return: HTTP response.
        """
        with autotest.step("PATCH /users/me/preferences"):
            return await self.api_client.patch("", json_data=data)
