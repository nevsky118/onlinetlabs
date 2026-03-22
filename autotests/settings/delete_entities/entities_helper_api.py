# Класс-обёртка с API-классами для удаления сущностей, созданных в тестах.

import httpx

from autotests.api.api_methods.gns3_service.gns3_sessions_api import Gns3SessionsApi
from autotests.api.api_methods.onlinetlabs_service.auth_api import AuthApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.configuration.config_model import ConfigModel


class EntitiesHelperApi:
    """
    Класс-обёртка, инкапсулирующий доступ ко всем API-классам, необходимым для удаления сущностей.
    Используется в системе автоматического удаления тестовых данных.
    """

    def __init__(self, config: ConfigModel = None):
        """
        Инициализация вспомогательных API-классов.

        :param config: Конфигурация окружения (ConfigModel).
        """
        self._config = config
        if config is not None:
            self.auth_api = AuthApi(config=config)
            self.sessions_api = SessionsApi(config=config)
            self.gns3_sessions_api = Gns3SessionsApi(config=config, base_url=config.gns3_base_url)

    async def delete_gns3_project(self, project_id: str) -> None:
        """Удалить GNS3 проект по ID через GNS3 server API."""
        if not self._config:
            return
        gns3_url = self._config.gns3_url
        async with httpx.AsyncClient() as client:
            auth = await client.post(
                f"{gns3_url}/v3/access/users/authenticate",
                json={
                    "username": self._config.gns3_admin_user,
                    "password": self._config.gns3_admin_password,
                },
            )
            jwt = auth.json().get("access_token", "")
            await client.delete(
                f"{gns3_url}/v3/projects/{project_id}",
                headers={"Authorization": f"Bearer {jwt}"},
            )
