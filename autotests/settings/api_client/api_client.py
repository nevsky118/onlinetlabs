# Generic async REST API client.

from urllib.parse import urljoin

from httpx import AsyncClient, Response

from autotests.settings.configuration.config_model import ConfigModel


def _get_controller_url(config: ConfigModel, name: str) -> str:
    """
    Builds the controller URL from base_url and the controller name.

    :param config: Configuration object holding base_url.
    :param name: Controller name (a path segment).
    :return: Full controller URL.
    """
    base_url = config.base_url
    if not base_url.endswith("/"):
        base_url += "/"
    return urljoin(base_url, name)


class ApiClient:
    """
    Generic async REST API client with JWT authorization.

    :param client: HTTP client (httpx.AsyncClient).
    :param config: Configuration model with environment parameters.
    :param account_name: Account name from config.accounts used for authorization.
    :param controller_path: Controller name (the path segment leading to the endpoints).
    :param service_name: Service name.
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
        Builds the full endpoint URL.

        :param path: Endpoint path relative to the base.
        :return: Full URL.
        """
        if not path:
            return self.base_url
        base = self.base_url
        if not base.endswith("/"):
            base += "/"
        return urljoin(base, path)

    def _get_headers(self, headers: dict = None) -> dict:
        """
        Builds request headers with authorization taken from config.accounts.

        :param headers: Custom headers. If None, they are generated automatically.
        :return: Dictionary of headers.
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
        Internal method that sends an HTTP request.

        :param method: HTTP method (GET, POST, PUT, DELETE, PATCH).
        :param path: Endpoint path relative to the base.
        :param headers: Request headers.
        :param json_data: JSON data in the request body.
        :param params: Query parameters of the request.
        :param data: Form data in the request body.
        :param kwargs: Additional parameters.
        :return: HTTP response.
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

    async def post_stream(
        self,
        path: str,
        json_data: dict = None,
        headers: dict = None,
    ) -> list[str]:
        """
        Performs a POST while reading an SSE stream (text/event-stream).

        :param path: Endpoint path relative to the base.
        :param json_data: JSON data in the request body.
        :param headers: Request headers.
        :return: List of response lines, including the empty SSE separator lines.
        """
        lines: list[str] = []
        async with self.client.stream(
            "POST",
            self._url(path),
            headers=self._get_headers(headers),
            json=json_data,
        ) as response:
            async for line in response.aiter_lines():
                lines.append(line)
        return lines

    async def get(self, path: str, **kwargs) -> Response:
        """
        Performs a GET request.

        :param path: Endpoint path relative to the base.
        :param kwargs: Additional request parameters.
        :return: HTTP response.
        """
        return await self._send_request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Response:
        """
        Performs a POST request.

        :param path: Endpoint path relative to the base.
        :param kwargs: Additional request parameters (json_data, headers, and so on).
        :return: HTTP response.
        """
        return await self._send_request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Response:
        """
        Performs a PUT request.

        :param path: Endpoint path relative to the base.
        :param kwargs: Additional request parameters.
        :return: HTTP response.
        """
        return await self._send_request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Response:
        """
        Performs a PATCH request.

        :param path: Endpoint path relative to the base.
        :param kwargs: Additional request parameters.
        :return: HTTP response.
        """
        return await self._send_request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Response:
        """
        Performs a DELETE request.

        :param path: Endpoint path relative to the base.
        :param kwargs: Additional request parameters.
        :return: HTTP response.
        """
        return await self._send_request("DELETE", path, **kwargs)
