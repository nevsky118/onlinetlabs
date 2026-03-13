# Sessions хелперы — композиция API-вызовов с данными и проверками.

from httpx import AsyncClient

from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.api.data.onlinetlabs_service.sessions_data_api import SessionCreateData
from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.delete_entities.entities_registry import EntitiesRegistry
from autotests.settings.delete_entities.entity_types import EntitiesTypes
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


class SessionsHelperApi:
    """
    Высокоуровневые операции с сессиями.

    :param client: HTTP-клиент для выполнения запросов.
    :param config: Объект ConfigModel с параметрами окружения.
    """

    def __init__(self, client: AsyncClient, config: ConfigModel):
        self.client = client
        self.config = config
        self.sessions_api = SessionsApi(client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.entities_registry = EntitiesRegistry(config=config)

    async def create_session(self, session_data: dict | None = None) -> dict:
        """
        Создание сессии с проверкой и регистрацией для очистки.

        :param session_data: Payload (если None — генерируется).
        :return: Данные созданной сессии.
        """
        if session_data is None:
            session_data = SessionCreateData().data

        with autotest.step("Создаём сессию"):
            response = await self.sessions_api.post_session(data=session_data)

        check_response_status(response, 201)

        result = response.json()

        self.entities_registry.add_id(
            ent_type=EntitiesTypes.session,
            ent_param=result.get("id"),
        )

        return result
