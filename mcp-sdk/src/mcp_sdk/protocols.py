"""Протоколы возможностей MCP-сервера."""

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from mcp_sdk.context import SessionContext
from mcp_sdk.models import (
    ActionResult,
    ActionSpec,
    Component,
    ComponentDetail,
    ErrorEntry,
    LogEntry,
    LogLevel,
    SystemOverview,
    UserAction,
)


@runtime_checkable
class StateProvider(Protocol):
    """Чтение состояния целевой системы. Обязательный протокол."""

    async def list_components(self, ctx: SessionContext) -> list[Component]: ...
    async def get_component(
        self, ctx: SessionContext, component_id: str
    ) -> ComponentDetail: ...
    async def get_system_overview(self, ctx: SessionContext) -> SystemOverview: ...


@runtime_checkable
class LogProvider(Protocol):
    """Логи ошибок и предупреждений целевой системы."""

    async def list_errors(
        self, ctx: SessionContext, since: datetime | None = None
    ) -> list[ErrorEntry]: ...
    async def get_logs(
        self, ctx: SessionContext, level: LogLevel = LogLevel.ALL, limit: int = 100
    ) -> list[LogEntry]: ...


@runtime_checkable
class HistoryProvider(Protocol):
    """История действий пользователя в целевой системе."""

    async def list_user_actions(
        self, ctx: SessionContext, limit: int = 50
    ) -> list[UserAction]: ...


@runtime_checkable
class ActionProvider(Protocol):
    """Выполнение действий в целевой системе."""

    async def list_available_actions(
        self, ctx: SessionContext, component_id: str | None = None
    ) -> list[ActionSpec]: ...
    async def execute_action(
        self, ctx: SessionContext, action_name: str, params: dict[str, Any]
    ) -> ActionResult: ...
