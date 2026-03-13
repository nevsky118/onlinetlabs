# Courses API — тонкие HTTP-обёртки для /courses/* эндпоинтов.

from httpx import AsyncClient, Response

from autotests.settings.api_client.api_client import ApiClient
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


class CoursesApi:
    """
    HTTP-обёртки для courses-эндпоинтов.

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
            controller_path="/courses",
        )

    async def get_courses(
        self,
        limit: int = 30,
        offset: int = 0,
    ) -> Response:
        """
        GET /courses — список курсов.

        :param limit: Макс. количество результатов.
        :param offset: Смещение для пагинации.
        :return: HTTP-ответ.
        """
        with autotest.step("GET /courses"):
            return await self.api_client.get("", params={
                "limit": limit,
                "offset": offset,
            })

    async def get_course_by_slug(self, slug: str) -> Response:
        """
        GET /courses/{slug} — получение курса по slug.

        :param slug: Slug курса.
        :return: HTTP-ответ.
        """
        with autotest.step(f"GET /courses/{slug}"):
            return await self.api_client.get(slug)
