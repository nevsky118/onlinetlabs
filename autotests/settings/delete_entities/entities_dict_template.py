# Entity dictionary template for EntitiesRegistry.

from autotests.settings.delete_entities.entity_types import EntitiesTypes


class EntitiesDictTemplate:
    """
    Creates the template for the entity dictionary structure.

    The key is the entity type, the value is an empty list.
    """

    @staticmethod
    def new_entities_dict() -> dict[str, list]:
        """
        Returns the entity dictionary template.

        :return: A dictionary with entity keys and empty lists.
        """
        return {
            # Order matters, the entities listed first are deleted first.
            EntitiesTypes.gns3_project.name: [],
            EntitiesTypes.gns3_session.name: [],
            EntitiesTypes.learning_session.name: [],
            EntitiesTypes.session.name: [],
            EntitiesTypes.user.name: [],
        }
