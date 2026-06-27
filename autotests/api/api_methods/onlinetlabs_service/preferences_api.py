# Preferences API — тонкие HTTP-обёртки для /users/me/preferences.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class PreferencesApi:
    """
    HTTP-обёртки для preferences-эндпоинтов.

    :param client: HTTP-клиент (httpx.AsyncClient).
    :param config: Объект ConfigModel с параметрами окружения.
    :param account_name: Название учётной записи из конфигурации.
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
        GET /users/me/preferences — настройки текущего пользователя.

        :return: HTTP-ответ.
        """
        with autotest.step("GET /users/me/preferences"):
            return await self.api_client.get("")

    async def patch_preferences(self, data: dict) -> Response:
        """
        PATCH /users/me/preferences — обновление настроек пользователя.

        :param data: Payload с настройками (например, default_model_id).
        :return: HTTP-ответ.
        """
        with autotest.step("PATCH /users/me/preferences"):
            return await self.api_client.patch("", json_data=data)
