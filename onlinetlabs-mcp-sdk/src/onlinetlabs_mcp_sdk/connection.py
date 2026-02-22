"""Управление подключениями к целевой системе."""

from abc import ABC, abstractmethod
from typing import Any

from onlinetlabs_mcp_sdk.errors import MCPServerError


class BaseConnectionManager(ABC):
    """Менеджер подключений к целевой системе."""

    @abstractmethod
    async def connect(self, environment_url: str) -> Any: ...
    @abstractmethod
    async def disconnect(self, connection: Any) -> None: ...
    @abstractmethod
    async def health_check(self, connection: Any) -> bool: ...


class ConnectionPool:
    """Пул подключений к целевым системам, per-environment_url."""

    def __init__(self, manager: BaseConnectionManager, max_size: int = 50):
        self._manager = manager
        self._max_size = max_size
        self._connections: dict[str, Any] = {}

    async def start(self) -> None:
        self._connections = {}

    async def get_connection(self, environment_url: str) -> Any:
        if environment_url in self._connections:
            return self._connections[environment_url]
        if len(self._connections) >= self._max_size:
            raise MCPServerError(
                f"Connection pool exhausted (max_size={self._max_size})"
            )
        conn = await self._manager.connect(environment_url)
        self._connections[environment_url] = conn
        return conn

    async def close(self) -> None:
        for conn in self._connections.values():
            await self._manager.disconnect(conn)
        self._connections.clear()
