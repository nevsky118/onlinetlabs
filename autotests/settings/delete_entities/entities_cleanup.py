# Логика удаления сущностей после тестов.

import logging

from autotests.settings.delete_entities.entities_helper_api import EntitiesHelperApi
from autotests.settings.delete_entities.entities_registry import EntitiesRegistry
from autotests.settings.delete_entities.entity_types import EntitiesTypes

logger = logging.getLogger("entities")


class EntitiesCleanup:
    """
    Удаление созданных в тестах сущностей по ID и имени.
    """

    def __init__(self):
        self.entities_helper_api = EntitiesHelperApi()
        self.entities_registry = EntitiesRegistry()

    async def delete_test_entities_by_id(self, test_name: str):
        """
        Удаляет сущности по сохранённым ID.

        :param test_name: Имя теста.
        """
        entities_ids = self.entities_registry.get_ids(test_name=test_name).items()

        for type_, ids_ in entities_ids:
            for id_ in ids_:
                try:
                    match type_:
                        case EntitiesTypes.gns3_session.name:
                            await self.entities_helper_api.gns3_sessions_api.delete_session(session_id=id_)
                        case EntitiesTypes.session.name:
                            await self.entities_helper_api.sessions_api.delete_session(session_id=id_)
                        case EntitiesTypes.user.name:
                            await self.entities_helper_api.auth_api.delete_user(user_id=id_)
                except Exception as ex:
                    logger.error(f"[DeleteByID] Не удалось удалить {type_} - {ex}")

    async def delete_test_entities_by_name(self, test_name: str):
        """
        Удаляет сущности по сохранённым именам (поиск ID → удаление).

        :param test_name: Имя теста.
        """
        entities_names = self.entities_registry.get_names(test_name=test_name).items()

        for type_, names in entities_names:
            for name in names:
                try:
                    match type_:
                        case EntitiesTypes.user.name:
                            logger.info(f"[DeleteByName] Ищем для удаления user - {name}")
                            # TODO: поиск ID по имени → удаление
                except Exception as ex:
                    logger.error(f"[DeleteByName] Ошибка при поиске {type_} - {ex}")


# Глобальный экземпляр
delete_test_entities = EntitiesCleanup()
