# Управление подключениями к целевой системе.

from abc import ABC, abstractmethod
from typing import Any

from mcp_sdk.context import SessionContext
from mcp_sdk.errors import MCPServerError


class BaseConnectionManager(ABC):
    """Менеджер подключений к целевой системе."""

    @abstractmethod
    async def connect(self, ctx: SessionContext) -> Any: ...
    @abstractmethod
    async def disconnect(self, connection: Any) -> None: ...
    @abstractmethod
    async def health_check(self, connection: Any) -> bool: ...


class ConnectionPool:
    """Пул подключений, per-(environment_url, user_id)."""

    def __init__(self, manager: BaseConnectionManager, max_size: int = 50):
        self._manager = manager
        self._max_size = max_size
        self._connections: dict[tuple[str, str], Any] = {}

    async def start(self) -> None:
        self._connections = {}

    def _key(self, ctx: SessionContext) -> tuple[str, str]:
        """Ключ пула: (environment_url, user_id)."""
        return (ctx.environment_url, ctx.user_id)

    async def get_connection(self, ctx: SessionContext) -> Any:
        key = self._key(ctx)
        if key in self._connections:
            return self._connections[key]
        if len(self._connections) >= self._max_size:
            raise MCPServerError(
                f"Connection pool exhausted (max_size={self._max_size})"
            )
        conn = await self._manager.connect(ctx)
        self._connections[key] = conn
        return conn

    async def close(self) -> None:
        for conn in self._connections.values():
            await self._manager.disconnect(conn)
        self._connections.clear()
