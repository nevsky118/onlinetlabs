# Шаблон словаря сущностей для EntitiesRegistry.

from autotests.settings.delete_entities.entity_types import EntitiesTypes


class EntitiesDictTemplate:
    """
    Создаёт шаблон структуры словаря сущностей.

    Ключ — тип сущности, значение — пустой список.
    """

    @staticmethod
    def new_entities_dict() -> dict[str, list]:
        """
        Возвращает шаблон словаря сущностей.

        :return: Словарь с ключами-сущностями и пустыми списками.
        """
        return {
            # Порядок важен: верхние сущности удаляются первыми.
            EntitiesTypes.gns3_project.name: [],
            EntitiesTypes.gns3_session.name: [],
            EntitiesTypes.session.name: [],
            EntitiesTypes.user.name: [],
        }
