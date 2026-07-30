# Test data generators for sessions.

from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class SessionCreateData(DataAbstractionGenerator):
    """
    Generates the payload for creating a session.

    :ivar lab_slug: Lab slug.
    :ivar data: Payload dictionary for the POST.
    """

    def __init__(self, lab_slug: str = None):
        uid = Randomizer.uuid()
        self.lab_slug = lab_slug or f"lab-{Randomizer.random_string(8).lower()}"

        self.data = {
            "lab_slug": self.lab_slug,
        }


class SessionUpdateData(DataAbstractionGenerator):
    """
    Generates the payload for updating a session status.

    :ivar status: New session status.
    :ivar data: Payload dictionary for the PATCH.
    """

    def __init__(self, status: str = "completed"):
        self.status = status

        self.data = {
            "status": self.status,
        }


class NodeActionData(DataAbstractionGenerator):
    """
    Generates the payload for the node action endpoints.

    :ivar action: Action name (start/stop/suspend/reset/reload).
    :ivar data: Empty payload, the action lives in the path parameter.
    """

    def __init__(self, action: str):
        self.action = action
        self.data = {}


class ActivityQueryData(DataAbstractionGenerator):
    """
    Generates the query parameters for GET activity.

    :ivar limit: Limit on the number of events.
    :ivar cursor: Pagination cursor (optional).
    :ivar data: Dictionary of query parameters.
    """

    def __init__(self, limit: int = 50, cursor: str | None = None):
        self.limit = limit
        self.cursor = cursor
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        self.data = params
