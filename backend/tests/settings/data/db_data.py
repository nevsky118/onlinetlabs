"""Test data for the database seam: session and result doubles the services talk to."""


class ScalarResultData:
    """A Result that answers with one prepared scalar and no rows."""

    def __init__(self, value=None, rows: list | None = None):
        self.value = value
        self.rows = rows or []

    def scalar_one_or_none(self):
        """The single prepared value."""
        return self.value

    def scalar(self):
        """The single prepared value."""
        return self.value

    def scalars(self):
        """Mimics Result.scalars()."""
        return self

    def all(self) -> list:
        """The prepared rows."""
        return list(self.rows)


class CapturingSessionData:
    """A db session that records what was added and answers every query with nothing."""

    def __init__(self, result: ScalarResultData | None = None):
        self.added: list = []
        self.result = result if result is not None else ScalarResultData()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def add(self, obj) -> None:
        """Records the row instead of writing it."""
        self.added.append(obj)

    async def commit(self) -> None:
        """Accepts the commit; nothing is persisted."""

    async def execute(self, statement):
        """Answers with the prepared result."""
        return self.result

    async def get(self, model, key):
        """No row exists."""
        return None


class NullDbSessionData:
    """A db session holding no rows, so a locale re-read falls back to the default."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, model, key):
        """No row exists."""
        return None


class UnreachableDbData:
    """A session factory that fails the way an unreachable database does."""

    def __call__(self):
        raise RuntimeError("db down")


class SessionLocaleRowData:
    """Stand-in for a LearningSession row, exposing only the locale the monitor reads."""

    def __init__(self, locale):
        self.locale = locale


class MutableRowDbSessionData:
    """A db session whose .get() returns whatever the holder currently points at."""

    def __init__(self, row_holder: dict, key: str = "row"):
        self.row_holder = row_holder
        self.key = key

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, model, key):
        """The row the holder points at right now."""
        return self.row_holder[self.key]
