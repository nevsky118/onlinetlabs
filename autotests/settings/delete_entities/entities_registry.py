# Singleton registry of entities created by the autotests.

from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.delete_entities.entities_dict_template import EntitiesDictTemplate
from autotests.settings.delete_entities.entity_types import EntitiesTypes
from autotests.settings.utils.singleton import Singleton
from autotests.settings.utils.utils import get_current_test_name


class EntitiesRegistry(metaclass=Singleton):
    """
    Manager that stores data about entities created by the autotests.

    Lets you add entities by ID or name, then read and clear the data after a test.
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
        Adds an entity name to the storage.

        :param ent_type: Entity type.
        :param ent_param: Entity name.
        """
        test_name = get_current_test_name()
        if test_name not in self._main_delete_dict:
            self.register_test(test_name)
        self._main_delete_dict[test_name]["names_dict"][ent_type.name].append(ent_param)

    def add_id(self, ent_type: EntitiesTypes, ent_param):
        """
        Adds an entity ID to the storage.

        :param ent_type: Entity type.
        :param ent_param: Entity ID.
        """
        test_name = get_current_test_name()
        if test_name not in self._main_delete_dict:
            self.register_test(test_name)
        self._main_delete_dict[test_name]["ids_dict"][ent_type.name].append(ent_param)

    def add_ids(self, ent_type: EntitiesTypes, ent_param: list):
        """
        Adds a list of entity IDs to the storage.

        :param ent_type: Entity type.
        :param ent_param: List of IDs.
        """
        test_name = get_current_test_name()
        if test_name not in self._main_delete_dict:
            self.register_test(test_name)
        self._main_delete_dict[test_name]["ids_dict"][ent_type.name].extend(ent_param)

    def add_data(self, ent_type: EntitiesTypes, ent_param: dict):
        """
        Adds entity data to the storage.

        :param ent_type: Entity type.
        :param ent_param: Entity data.
        """
        test_name = get_current_test_name()
        if test_name not in self._main_delete_dict:
            self.register_test(test_name)
        self._main_delete_dict[test_name]["data_dict"][ent_type.name].append(ent_param)

    def get_names(self, test_name: str) -> dict[str, list]:
        """
        Gets all entity names for a test.

        :param test_name: Test name.
        :return: Dictionary of names.
        """
        return self._main_delete_dict[test_name]["names_dict"]

    def get_ids(self, test_name: str) -> dict[str, list]:
        """
        Gets all entity IDs for a test.

        :param test_name: Test name.
        :return: Dictionary of IDs.
        """
        return self._main_delete_dict[test_name]["ids_dict"]

    def get_ids_by_name(self, test_name: str) -> dict[str, list]:
        """
        Gets all IDs keyed by name for a test.

        :param test_name: Test name.
        :return: Dictionary of IDs by name.
        """
        return self._main_delete_dict[test_name]["ids_name_dict"]

    def get_data(self, test_name: str) -> dict[str, list]:
        """
        Gets all entity data for a test.

        :param test_name: Test name.
        :return: Dictionary of data.
        """
        return self._main_delete_dict[test_name]["data_dict"]

    def get_config(self) -> ConfigModel:
        """
        Returns the stored configuration.

        :return: ConfigModel.
        """
        return self._config

    def has_test(self, test_name: str) -> bool:
        """
        Checks whether entities exist for a test.

        :param test_name: Test name.
        :return: True if there is data.
        """
        return test_name in self._main_delete_dict
