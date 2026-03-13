# Auth API — тонкие HTTP-обёртки для /auth/* эндпоинтов.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class AuthApi:
    """
    HTTP-обёртки для auth-эндпоинтов.

    :param client: HTTP-клиент (httpx.AsyncClient).
    :param config: Объект ConfigModel с параметрами окружения.
    :param account_name: Название учётной записи из конфигурации.
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
        POST /auth/register — регистрация пользователя.

        :param data: Словарь с полями email, password, name.
        :return: HTTP-ответ с данными зарегистрированного пользователя.
        """
        with autotest.step("POST /auth/register"):
            return await self.api_client.post("register", json_data=data)

    async def post_login(self, data: dict) -> Response:
        """
        POST /auth/login — авторизация пользователя.

        :param data: Словарь с полями email, password.
        :return: HTTP-ответ с данными авторизованного пользователя.
        """
        with autotest.step("POST /auth/login"):
            return await self.api_client.post("login", json_data=data)

    async def post_exchange(self, data: dict) -> Response:
        """
        POST /auth/exchange — обмен учётных данных на JWT.

        :param data: Словарь с полями user_id, email.
        :return: HTTP-ответ с JWT-токеном.
        """
        with autotest.step("POST /auth/exchange"):
            return await self.api_client.post("exchange", json_data=data)

    async def delete_user(self, user_id: str) -> Response:
        """
        DELETE /auth/users/{user_id} — удаление пользователя.

        :param user_id: Идентификатор пользователя.
        :return: HTTP-ответ.
        """
        with autotest.step(f"DELETE /auth/users/{user_id}"):
            return await self.api_client.delete(f"users/{user_id}")
