# Progress API — тонкие HTTP-обёртки для /users/me/progress/* эндпоинтов.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class ProgressApi:
    """
    HTTP-обёртки для progress-эндпоинтов.

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
            controller_path="/users/me/progress",
        )

    async def get_progress(
        self,
        limit: int = 30,
        offset: int = 0,
    ) -> Response:
        """
        GET /users/me/progress — общий прогресс пользователя.

        :param limit: Макс. количество результатов.
        :param offset: Смещение для пагинации.
        :return: HTTP-ответ.
        """
        with autotest.step("GET /users/me/progress"):
            return await self.api_client.get("", params={
                "limit": limit,
                "offset": offset,
            })

    async def get_lab_progress(self, lab_slug: str) -> Response:
        """
        GET /users/me/progress/labs/{lab_slug} — прогресс по конкретной лабораторной.

        :param lab_slug: Slug лабораторной работы.
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /users/me/progress/labs/{lab_slug}"):
            return await self.api_client.get(f"labs/{lab_slug}")

    async def post_start_lab(self, lab_slug: str) -> Response:
        """
        POST /users/me/progress/labs/{lab_slug}/start — начать лабораторную.

        :param lab_slug: Slug лабораторной работы.
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /users/me/progress/labs/{lab_slug}/start"):
            return await self.api_client.post(f"labs/{lab_slug}/start")

    async def post_step_attempt(self, lab_slug: str, step_slug: str, data: dict) -> Response:
        """
        POST /users/me/progress/labs/{lab_slug}/steps/{step_slug}/attempt — попытка шага.

        :param lab_slug: Slug лабораторной работы.
        :param step_slug: Slug шага.
        :param data: Payload с ответом.
        :return: HTTP-ответ.
        """
        with autotest.step(f"POST /users/me/progress/labs/{lab_slug}/steps/{step_slug}/attempt"):
            return await self.api_client.post(
                f"labs/{lab_slug}/steps/{step_slug}/attempt",
                json_data=data,
            )
