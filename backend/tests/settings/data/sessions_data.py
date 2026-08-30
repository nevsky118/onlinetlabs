"""Test data for the session lifecycle: database doubles the services talk to."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from sqlalchemy.exc import IntegrityError
from starlette.websockets import WebSocketDisconnect


class ConflictingDbSessionData:
    """A db session whose commit hits the partial unique index on live sessions."""

    def __init__(self, constraint: str = "uq_learning_sessions_one_live"):
        self.constraint = constraint
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def add(self, _row) -> None:
        """Accepts the row; the conflict surfaces on commit."""

    async def commit(self) -> None:
        """Raises the way Postgres does on a duplicate live session."""
        raise IntegrityError("INSERT", {}, Exception(self.constraint))

    async def rollback(self) -> None:
        """Records that the caller unwound the transaction."""
        self.rolled_back = True

    async def refresh(self, _row) -> None:
        """Never reached in this scenario."""


class SqlCapturingDbData:
    """A db session that records the statement it was given and returns no rows."""

    def __init__(self):
        self.statements: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, statement):
        """Stores the rendered SQL and answers with an empty result."""
        self.statements.append(str(statement))
        return self

    def scalars(self):
        """Mimics Result.scalars()."""
        return self

    def all(self) -> list:
        """No rows matched."""
        return []


class StateCacheData:
    """A session-state cache that never has a hit and never stores."""

    async def get(self, session_id):
        """Always a miss."""
        return None

    async def set(self, session_id, value):
        """Accepts the write and drops it."""
        return None


class ActivityLogData:
    """An activity log that replays a fixed history."""

    def __init__(self, events: list):
        self.events = events

    async def history(self, session_id, since, limit) -> list:
        """The prepared events, regardless of the window asked for."""
        return self.events


class WebSocketData:
    """Minimal websocket stub. With a gateway it also answers close/receive_text."""

    def __init__(self, gateway=None):
        self.accept = AsyncMock()
        self.close = AsyncMock()
        # receive_text drops the connection at once, so a handler missing its
        # ownership check cannot hang in `while True`.
        self.receive_text = AsyncMock(side_effect=WebSocketDisconnect())
        self.app = SimpleNamespace(state=SimpleNamespace(gateway=gateway))


class ProvisioningGns3Data:
    """A GNS3 client that provisions one session and records the node actions asked of it."""

    def __init__(self, session_id: str = "gns3-sid-1", fail_bulk: bool = False):
        self.session_id = session_id
        self.fail_bulk = fail_bulk
        self.bulk_actions: list[tuple[str, str]] = []

    async def create_session(self, user_id: str, template_project_id: str) -> dict:
        """Returns the shape launch_session stores in session meta."""
        return {
            "session_id": self.session_id,
            "gns3_user_id": "gns3-user-1",
            "gns3_username": "student-1",
            "project_id": "project-1",
            "gns3_password": "pw",
            "gns3_jwt": "jwt",
        }

    async def bulk_node_action(self, session_id: str, action: str) -> None:
        """Records the action, or fails when the double is set up to."""
        self.bulk_actions.append((session_id, action))
        if self.fail_bulk:
            raise RuntimeError("gns3 refused the bulk action")
