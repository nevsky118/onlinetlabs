# Data generators for the console history endpoints.

from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class ConsoleCommandsQueryData(DataAbstractionGenerator):
    """
    Query parameters for GET /sessions/{id}/console-commands.

    :ivar limit: Max. number of commands to return.
    :ivar node_id: Restrict results to one node (None for all nodes).
    :ivar data: Dictionary of query parameters.
    """

    def __init__(self, limit: int = 50, node_id: str | None = None):
        self.limit = limit
        self.node_id = node_id
        params: dict = {"limit": limit}
        if node_id:
            params["node_id"] = node_id
        self.data = params


class UnknownSessionData(DataAbstractionGenerator):
    """
    A session id that cannot exist.

    :ivar session_id: Random UUID not tied to any created session.
    :ivar data: Dictionary holding the session id.
    """

    def __init__(self):
        self.session_id = Randomizer.uuid()
        self.data = {"session_id": self.session_id}


class UnknownNodeData(DataAbstractionGenerator):
    """
    A node id that cannot exist.

    :ivar node_id: Random UUID not tied to any created node.
    :ivar data: Dictionary holding the node id.
    """

    def __init__(self):
        self.node_id = Randomizer.uuid()
        self.data = {"node_id": self.node_id}
