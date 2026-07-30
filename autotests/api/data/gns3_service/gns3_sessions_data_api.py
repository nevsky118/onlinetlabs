# Data generators for GNS3 sessions.

from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class Gns3SessionCreateData(DataAbstractionGenerator):
    """
    Generates the payload for POST /sessions.

    :ivar user_id: Platform user ID.
    :ivar lab_template_project_id: UUID of the GNS3 template project.
    :ivar data: Payload dictionary for the POST.
    """

    def __init__(self, user_id: str = None, lab_template_project_id: str = None):
        self.user_id = user_id or f"user-{Randomizer.random_string(6).lower()}"
        self.lab_template_project_id = lab_template_project_id or Randomizer.uuid()

        self.data = {
            "user_id": self.user_id,
            "lab_template_project_id": self.lab_template_project_id,
        }


class NodeActionData(DataAbstractionGenerator):
    """
    Describes an action on a node (start/stop/suspend/reload).

    :ivar action: Action name.
    :ivar data: Empty payload, the action is passed in the URL.
    """

    def __init__(self, action: str):
        self.action = action
        self.data = {}


class ActivityQueryData(DataAbstractionGenerator):
    """
    Query parameters for GET /sessions/{id}/activity.

    :ivar limit: Event limit.
    :ivar cursor: Pagination cursor.
    :ivar data: Dictionary of query parameters.
    """

    def __init__(self, limit: int = 50, cursor: str | None = None):
        self.limit = limit
        self.cursor = cursor
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        self.data = params
