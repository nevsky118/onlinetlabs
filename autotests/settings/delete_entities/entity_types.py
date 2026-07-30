# Enumeration of entity types used by the automatic cleanup.

from enum import Enum


class EntitiesTypes(Enum):
    """
    Types of entities created by the tests.

    Order matters, the ones listed first are deleted first.
    """

    gns3_project = "gns3_project"
    gns3_session = "gns3_session"
    learning_session = "learning_session"
    session = "session"
    user = "user"
