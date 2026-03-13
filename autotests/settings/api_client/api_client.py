# Универсальный async REST API клиент.

from urllib.parse import urljoin

from httpx import AsyncClient, Response

from autotests.settings.configuration.config_model import ConfigModel


def _get_controller_url(config: ConfigModel, name: str) -> str:
    """
    Формирует URL-адрес контроллера на основе base_url и имени контроллера.

    :param config: Объект конфигурации с base_url.
    :param name: Название контроллера (часть пути).
    :return: Полный URL-адрес контроллера.
    """
    base_url = config.base_url
    if not base_url.endswith("/"):
        base_url += "/"
    return urljoin(base_url, name)


class ApiClient:
    """
    Универсальный async REST API клиент с авторизацией через JWT.

    :param client: HTTP-клиент (httpx.AsyncClient).
    :param config: Конфигурационная модель с параметрами окружения.
    :param account_name: Имя аккаунта из config.accounts для авторизации.
    :param controller_path: Название контроллера (часть пути до эндпоинтов).
    :param service_name: Имя сервиса.
    """

    def __init__(
        self,
        client: AsyncClient = None,
        config: ConfigModel = None,
        account_name: str = "",
        controller_path: str = "",
        service_name: str = "",
        base_url: str = "",
    ):
        self.client = client or AsyncClient()
        self.config = config
        self.account_name = account_name
        self.controller_path = controller_path
        self.service_name = service_name

        if base_url:
            effective_base = base_url
            if not effective_base.endswith("/"):
                effective_base += "/"
            self.base_url = urljoin(effective_base, controller_path) if controller_path else effective_base
        else:
            self.base_url = _get_controller_url(config, controller_path) if controller_path else config.base_url

    def _url(self, path: str) -> str:
        """
        Формирует полный URL эндпоинта.

        :param path: Относительный путь до эндпоинта.
        :return: Полный URL.
        """
        if not path:
            return self.base_url
        base = self.base_url
        if not base.endswith("/"):
            base += "/"
        return urljoin(base, path)

    def _get_headers(self, headers: dict = None) -> dict:
        """
        Формирует заголовки запроса с авторизацией из config.accounts.

        :param headers: Пользовательские заголовки (если None — генерируются автоматически).
        :return: Словарь заголовков.
        """
        if headers is not None:
            return headers

        result = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.account_name and self.account_name in self.config.accounts:
            token = self.config.accounts[self.account_name].token
            if token:
                result["Authorization"] = f"Bearer {token}"

        return result

    async def _send_request(
        self,
        method: str,
        path: str,
        headers: dict = None,
        json_data: dict = None,
        params: dict = None,
        data: dict = None,
        **kwargs,
    ) -> Response:
        """
        Внутренний метод отправки HTTP-запроса.

        :param method: HTTP-метод (GET, POST, PUT, DELETE, PATCH).
        :param path: Относительный путь эндпоинта.
        :param headers: Заголовки запроса.
        :param json_data: JSON-данные в теле запроса.
        :param params: Query-параметры запроса.
        :param data: Form-данные в теле запроса.
        :param kwargs: Дополнительные параметры.
        :return: HTTP-ответ.
        """
        clean_params = {k: v for k, v in params.items() if v is not None} if params else None
        return await self.client.request(
            method=method,
            url=self._url(path),
            headers=self._get_headers(headers),
            json=json_data,
            params=clean_params,
            data=data,
            **kwargs,
        )

    async def get(self, path: str, **kwargs) -> Response:
        """
        Выполняет GET-запрос.

        :param path: Относительный путь до эндпоинта.
        :param kwargs: Дополнительные параметры запроса.
        :return: HTTP-ответ.
        """
        return await self._send_request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Response:
        """
        Выполняет POST-запрос.

        :param path: Относительный путь до эндпоинта.
        :param kwargs: Дополнительные параметры запроса (json_data, headers и т.д.).
        :return: HTTP-ответ.
        """
        return await self._send_request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Response:
        """
        Выполняет PUT-запрос.

        :param path: Относительный путь до эндпоинта.
        :param kwargs: Дополнительные параметры запроса.
        :return: HTTP-ответ.
        """
        return await self._send_request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Response:
        """
        Выполняет PATCH-запрос.

        :param path: Относительный путь до эндпоинта.
        :param kwargs: Дополнительные параметры запроса.
        :return: HTTP-ответ.
        """
        return await self._send_request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Response:
        """
        Выполняет DELETE-запрос.

        :param path: Относительный путь до эндпоинта.
        :param kwargs: Дополнительные параметры запроса.
        :return: HTTP-ответ.
        """
        return await self._send_request("DELETE", path, **kwargs)
