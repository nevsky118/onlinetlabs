# Auth хелперы — композиция API-вызовов с данными и проверками.

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
    Высокоуровневые auth-операции: регистрация, логин, exchange.

    :param client: HTTP-клиент для выполнения запросов.
    :param config: Объект ConfigModel с параметрами окружения.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel):
        self.client = client
        self.config = config
        self.auth_api = AuthApi(client, config)
        self.entities_registry = EntitiesRegistry(config=config)

    async def register_user(self, register_data: dict | None = None) -> dict:
        """
        Регистрация нового пользователя.

        :param register_data: Словарь с полями email, password, name (если None — генерируется автоматически).
        :return: Словарь UserResponse с полями id, email, name.
        """
        if register_data is None:
            register_data = AuthRegisterData().data

        with autotest.step("Регистрация пользователя"):
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
        Логин по учётным данным.

        :param login_data: Словарь с полями email, password (если None — генерируется автоматически).
        :return: Словарь UserResponse с полями id, email, name.
        """
        if login_data is None:
            login_data = AuthLoginData().data

        with autotest.step("Логин пользователя"):
            response = await self.auth_api.post_login(data=login_data)

        check_response_status(response, 200)
        return response.json()

    async def exchange_token(self, exchange_data: dict | None = None) -> dict:
        """
        Обмен учётных данных на JWT.

        :param exchange_data: Словарь с полями user_id, email (если None — генерируется автоматически).
        :return: Словарь TokenResponse с полями access_token, token_type.
        """
        if exchange_data is None:
            exchange_data = AuthExchangeData().data

        with autotest.step("Обмен токена"):
            response = await self.auth_api.post_exchange(data=exchange_data)

        check_response_status(response, 200)
        return response.json()
