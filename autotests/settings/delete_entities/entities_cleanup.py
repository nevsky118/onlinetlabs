# Logic for deleting entities after the tests.

import logging

from autotests.settings.delete_entities.entities_helper_api import EntitiesHelperApi
from autotests.settings.delete_entities.entities_registry import EntitiesRegistry
from autotests.settings.delete_entities.entity_types import EntitiesTypes

logger = logging.getLogger("entities")


class EntitiesCleanup:
    """
    Deletion of entities created by the tests, by ID and by name.
    """

    def __init__(self):
        self.entities_helper_api = EntitiesHelperApi()
        self.entities_registry = EntitiesRegistry()

    async def delete_test_entities_by_id(self, test_name: str):
        """
        Deletes entities by their stored IDs.

        :param test_name: Test name.
        """
        entities_ids = self.entities_registry.get_ids(test_name=test_name).items()

        for type_, ids_ in entities_ids:
            for id_ in ids_:
                try:
                    match type_:
                        case EntitiesTypes.gns3_project.name:
                            await self.entities_helper_api.delete_gns3_project(project_id=id_)
                        case EntitiesTypes.gns3_session.name:
                            await self.entities_helper_api.gns3_sessions_api.delete_session(session_id=id_)
                        case EntitiesTypes.learning_session.name:
                            await self.entities_helper_api.sessions_api.post_end(session_id=id_)
                        case EntitiesTypes.session.name:
                            await self.entities_helper_api.sessions_api.delete_session(session_id=id_)
                        case EntitiesTypes.user.name:
                            await self.entities_helper_api.auth_api.delete_user(user_id=id_)
                except Exception as ex:
                    logger.error(f"[DeleteByID] Failed to delete {type_} - {ex}")

    async def delete_test_entities_by_name(self, test_name: str):
        """
        Deletes entities by their stored names, looking up the ID and then deleting.

        :param test_name: Test name.
        """
        entities_names = self.entities_registry.get_names(test_name=test_name).items()

        for type_, names in entities_names:
            for name in names:
                try:
                    match type_:
                        case EntitiesTypes.user.name:
                            logger.info(f"[DeleteByName] Looking up user to delete - {name}")
                            # TODO: look up the ID by name, then delete
                except Exception as ex:
                    logger.error(f"[DeleteByName] Lookup failed for {type_} - {ex}")


# Global instance
delete_test_entities = EntitiesCleanup()
