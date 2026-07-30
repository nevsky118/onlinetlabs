# Auth API. Thin HTTP wrappers for the /auth/* endpoints.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class AuthApi:
    """
    HTTP wrappers for the auth endpoints.

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
            controller_path="/auth",
        )

    async def post_register(self, data: dict) -> Response:
        """
        POST /auth/register. Registers a user.

        :param data: Dictionary with the email, password, name fields.
        :return: HTTP response with the registered user data.
        """
        with autotest.step("POST /auth/register"):
            return await self.api_client.post("register", json_data=data)

    async def post_login(self, data: dict) -> Response:
        """
        POST /auth/login. Authenticates a user.

        :param data: Dictionary with the email, password fields.
        :return: HTTP response with the authenticated user data.
        """
        with autotest.step("POST /auth/login"):
            return await self.api_client.post("login", json_data=data)

    async def post_exchange(self, data: dict) -> Response:
        """
        POST /auth/exchange. Exchanges credentials for a JWT.

        :param data: Dictionary with the user_id, email fields.
        :return: HTTP response with the JWT token.
        """
        with autotest.step("POST /auth/exchange"):
            return await self.api_client.post("exchange", json_data=data)

    async def delete_user(self, user_id: str) -> Response:
        """
        DELETE /auth/users/{user_id}. Deletes a user.

        :param user_id: User identifier.
        :return: HTTP response.
        """
        with autotest.step(f"DELETE /auth/users/{user_id}"):
            return await self.api_client.delete(f"users/{user_id}")
