# Singleton-реестр сущностей, созданных в автотестах.

from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.delete_entities.entities_dict_template import EntitiesDictTemplate
from autotests.settings.delete_entities.entity_types import EntitiesTypes
from autotests.settings.utils.singleton import Singleton
from autotests.settings.utils.utils import get_current_test_name


class EntitiesRegistry(metaclass=Singleton):
    """
    Менеджер хранения данных о сущностях, созданных в автотестах.

    Позволяет добавлять сущности по ID/имени, получать и очищать данные после теста.
    """

    _main_delete_dict: dict = {}
    _config: ConfigModel = None

    def __init__(self, config: ConfigModel = None):
        if config is not None:
            self._config = config

    def register_test(self, test_name: str):
        self._main_delete_dict[test_name] = {
            "names_dict": EntitiesDictTemplate().new_entities_dict(),
            "ids_dict": EntitiesDictTemplate().new_entities_dict(),
            "ids_name_dict": EntitiesDictTemplate().new_entities_dict(),
            "data_dict": EntitiesDictTemplate().new_entities_dict(),
        }

    def unregister_test(self, test_name: str):
        self._main_delete_dict.pop(test_name, None)

    def add_name(self, ent_type: EntitiesTypes, ent_param: str):
        """
        Добавляет наименование сущности в хранилище.

        :param ent_type: Тип сущности.
        :param ent_param: Наименование сущности.
        """
        test_name = get_current_test_name()
        if test_name not in self._main_delete_dict:
            self.register_test(test_name)
        self._main_delete_dict[test_name]["names_dict"][ent_type.name].append(ent_param)

    def add_id(self, ent_type: EntitiesTypes, ent_param):
        """
        Добавляет ID сущности в хранилище.

        :param ent_type: Тип сущности.
        :param ent_param: ID сущности.
        """
        test_name = get_current_test_name()
        if test_name not in self._main_delete_dict:
            self.register_test(test_name)
        self._main_delete_dict[test_name]["ids_dict"][ent_type.name].append(ent_param)

    def add_ids(self, ent_type: EntitiesTypes, ent_param: list):
        """
        Добавляет список ID сущностей в хранилище.

        :param ent_type: Тип сущности.
        :param ent_param: Список ID.
        """
        test_name = get_current_test_name()
        if test_name not in self._main_delete_dict:
            self.register_test(test_name)
        self._main_delete_dict[test_name]["ids_dict"][ent_type.name].extend(ent_param)

    def add_data(self, ent_type: EntitiesTypes, ent_param: dict):
        """
        Добавляет данные сущности в хранилище.

        :param ent_type: Тип сущности.
        :param ent_param: Данные сущности.
        """
        test_name = get_current_test_name()
        if test_name not in self._main_delete_dict:
            self.register_test(test_name)
        self._main_delete_dict[test_name]["data_dict"][ent_type.name].append(ent_param)

    def get_names(self, test_name: str) -> dict[str, list]:
        """
        Получает все наименования сущностей для теста.

        :param test_name: Имя теста.
        :return: Словарь наименований.
        """
        return self._main_delete_dict[test_name]["names_dict"]

    def get_ids(self, test_name: str) -> dict[str, list]:
        """
        Получает все ID сущностей для теста.

        :param test_name: Имя теста.
        :return: Словарь ID.
        """
        return self._main_delete_dict[test_name]["ids_dict"]

    def get_ids_by_name(self, test_name: str) -> dict[str, list]:
        """
        Получает все ID по наименованию для теста.

        :param test_name: Имя теста.
        :return: Словарь ID по именам.
        """
        return self._main_delete_dict[test_name]["ids_name_dict"]

    def get_data(self, test_name: str) -> dict[str, list]:
        """
        Получает все данные сущностей для теста.

        :param test_name: Имя теста.
        :return: Словарь данных.
        """
        return self._main_delete_dict[test_name]["data_dict"]

    def get_config(self) -> ConfigModel:
        """
        Возвращает сохранённую конфигурацию.

        :return: ConfigModel.
        """
        return self._config

    def has_test(self, test_name: str) -> bool:
        """
        Проверяет наличие сущностей для теста.

        :param test_name: Имя теста.
        :return: True, если есть данные.
        """
        return test_name in self._main_delete_dict
