# Progress хелперы — композиция API-вызовов с данными и проверками.

from httpx import AsyncClient

from autotests.api.api_methods.onlinetlabs_service.progress_api import ProgressApi
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


class ProgressHelperApi:
    """
    Высокоуровневые операции с прогрессом.

    :param client: HTTP-клиент для выполнения запросов.
    :param config: Объект ConfigModel с параметрами окружения.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel):
        self.client = client
        self.config = config
        self.progress_api = ProgressApi(client, config, ConstantsSettings.REGISTERED_ACCOUNT)

    async def start_lab(self, lab_slug: str) -> dict:
        """
        Начать лабораторную работу с проверкой.

        :param lab_slug: Slug лабораторной работы.
        :return: Данные прогресса.
        """
        with autotest.step("Начинаем лабораторную"):
            response = await self.progress_api.post_start_lab(lab_slug=lab_slug)

        check_response_status(response, 201)
        return response.json()
