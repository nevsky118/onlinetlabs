# Auth helpers. Composition of API calls with data and checks.

from httpx import AsyncClient

from autotests.api.api_methods.onlinetlabs_service.auth_api import AuthApi
from autotests.api.data.onlinetlabs_service.auth_data_api import AuthRegisterData, AuthLoginData, AuthExchangeData
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.delete_entities.entities_registry import EntitiesRegistry
from autotests.settings.delete_entities.entity_types import EntitiesTypes
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


class AuthHelperApi:
    """
    High-level auth operations, namely registration, login and exchange.

    :param client: HTTP client used to perform the requests.
    :param config: ConfigModel object with the environment parameters.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel):
        self.client = client
        self.config = config
        self.auth_api = AuthApi(client, config)
        self.entities_registry = EntitiesRegistry(config=config)

    async def register_user(self, register_data: dict | None = None) -> dict:
        """
        Registers a new user.

        :param register_data: Dictionary with the email, password, name fields (generated automatically when None).
        :return: UserResponse dictionary with the id, email, name fields.
        """
        if register_data is None:
            register_data = AuthRegisterData().data

        with autotest.step("Register the user"):
            response = await self.auth_api.post_register(data=register_data)

        check_response_status(response, 201)

        user = response.json()
        self.entities_registry.add_id(
            ent_type=EntitiesTypes.user,
            ent_param=user.get("id"),
        )

        return user

    async def login_user(self, login_data: dict | None = None) -> dict:
        """
        Logs in with credentials.

        :param login_data: Dictionary with the email, password fields (generated automatically when None).
        :return: UserResponse dictionary with the id, email, name fields.
        """
        if login_data is None:
            login_data = AuthLoginData().data

        with autotest.step("Log in the user"):
            response = await self.auth_api.post_login(data=login_data)

        check_response_status(response, 200)
        return response.json()

    async def exchange_token(self, exchange_data: dict | None = None) -> dict:
        """
        Exchanges credentials for a JWT.

        :param exchange_data: Dictionary with the user_id, email fields (generated automatically when None).
        :return: TokenResponse dictionary with the access_token, token_type fields.
        """
        if exchange_data is None:
            exchange_data = AuthExchangeData().data

        with autotest.step("Exchange the token"):
            response = await self.auth_api.post_exchange(data=exchange_data)

        check_response_status(response, 200)
        return response.json()
