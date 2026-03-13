# Класс-обёртка с API-классами для удаления сущностей, созданных в тестах.

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
        if config is not None:
            self.auth_api = AuthApi(config=config)
            self.sessions_api = SessionsApi(config=config)
            self.gns3_sessions_api = Gns3SessionsApi(config=config, base_url=config.gns3_base_url)
