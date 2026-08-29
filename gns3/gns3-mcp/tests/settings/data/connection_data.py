"""Test data for the connection pool: a controllable clock and a counting manager."""

from mcp_sdk.connection import BaseConnectionManager


class FakeClockData:
    """Controllable clock that substitutes the time module inside mcp_sdk.connection."""

    def __init__(self, start: float = 1000.0):
        self.now = start

    def monotonic(self) -> float:
        """The current fake time."""
        return self.now

    def advance(self, seconds: float) -> None:
        """Moves the clock forward."""
        self.now += seconds


class CountingConnectionManagerData(BaseConnectionManager):
    """A manager that counts connects, disconnects and health checks."""

    def __init__(self, alive: bool = True):
        self.connects = 0
        self.disconnected: list = []
        self.health_calls = 0
        self.alive = alive

    async def connect(self, ctx):
        """Hands out a fresh numbered connection."""
        self.connects += 1
        return {"id": f"conn-{self.connects}", "user": ctx.user_id}

    async def disconnect(self, connection) -> None:
        """Records the connection that was closed."""
        self.disconnected.append(connection)

    async def health_check(self, connection) -> bool:
        """Reports the prepared liveness."""
        self.health_calls += 1
        return self.alive
