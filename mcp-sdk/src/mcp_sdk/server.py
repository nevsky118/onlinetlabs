"""Конструктор MCP-сервера с автоматическим обнаружением протоколов."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from mcp_sdk.context import ServerCapabilities, SessionContext
from mcp_sdk.errors import MCPServerError, SessionContextError
from mcp_sdk.models import LogLevel
from mcp_sdk.protocols import (
    ActionProvider,
    HistoryProvider,
    LogProvider,
    StateProvider,
)

logger = logging.getLogger(__name__)


class OnlinetlabsMCPServer:
    """Обёртка над FastMCP с автообнаружением протоколов и регистрацией инструментов."""

    def __init__(self, name: str, implementation: Any, **fastmcp_kwargs: Any) -> None:
        self._name = name
        self._impl = implementation
        self._capabilities: set[str] = set()
        self._domain_tool_names: list[str] = []
        self._tool_names: list[str] = []
        self._mcp = FastMCP(name, **fastmcp_kwargs)

        self._validate_minimum()
        self._discover_and_register()

    # Validation

    def _validate_minimum(self) -> None:
        """Реализация должна удовлетворять минимум StateProvider."""
        if not isinstance(self._impl, StateProvider):
            raise ValueError(
                f"Implementation must satisfy StateProvider protocol. "
                f"Got {type(self._impl).__name__}"
            )

    # Discovery & registration

    def _discover_and_register(self) -> None:
        """Интроспекция протоколов и регистрация соответствующих MCP-инструментов."""
        # StateProvider — всегда (проверен в _validate_minimum)
        self._capabilities.add("state")
        self._register_state_tools()

        if isinstance(self._impl, LogProvider):
            self._capabilities.add("logs")
            self._register_log_tools()

        if isinstance(self._impl, HistoryProvider):
            self._capabilities.add("history")
            self._register_history_tools()

        if isinstance(self._impl, ActionProvider):
            self._capabilities.add("actions")
            self._register_action_tools()

        # Мета-инструмент — всегда
        self._register_capabilities_tool()

    # State tools

    def _register_state_tools(self) -> None:
        impl = self._impl

        @self._mcp.tool(description="List all components in the system")
        async def list_components(ctx: dict[str, Any]) -> list[dict[str, Any]]:
            try:
                session = SessionContext(**ctx)
                result = await impl.list_components(session)
                return [c.model_dump(mode="json") for c in result]
            except ValidationError as e:
                raise SessionContextError(f"Invalid session context: {e}") from e
            except MCPServerError:
                raise
            except Exception:
                logger.exception("Unexpected error in list_components")
                raise MCPServerError("Internal server error") from None

        self._tool_names.append("list_components")

        @self._mcp.tool(
            description="Get detailed information about a specific component"
        )
        async def get_component(
            ctx: dict[str, Any], component_id: str
        ) -> dict[str, Any]:
            try:
                session = SessionContext(**ctx)
                result = await impl.get_component(session, component_id)
                return result.model_dump(mode="json")
            except ValidationError as e:
                raise SessionContextError(f"Invalid session context: {e}") from e
            except MCPServerError:
                raise
            except Exception:
                logger.exception("Unexpected error in get_component")
                raise MCPServerError("Internal server error") from None

        self._tool_names.append("get_component")

        @self._mcp.tool(description="Get a high-level overview of the entire system")
        async def get_system_overview(ctx: dict[str, Any]) -> dict[str, Any]:
            try:
                session = SessionContext(**ctx)
                result = await impl.get_system_overview(session)
                return result.model_dump(mode="json")
            except ValidationError as e:
                raise SessionContextError(f"Invalid session context: {e}") from e
            except MCPServerError:
                raise
            except Exception:
                logger.exception("Unexpected error in get_system_overview")
                raise MCPServerError("Internal server error") from None

        self._tool_names.append("get_system_overview")

    # Log tools

    def _register_log_tools(self) -> None:
        impl = self._impl

        @self._mcp.tool(description="List recent errors and warnings")
        async def list_errors(
            ctx: dict[str, Any],
            since: str | None = None,
        ) -> list[dict[str, Any]]:
            try:
                session = SessionContext(**ctx)
                since_dt = datetime.fromisoformat(since) if since else None
                result = await impl.list_errors(session, since=since_dt)
                return [e.model_dump(mode="json") for e in result]
            except ValidationError as e:
                raise SessionContextError(f"Invalid session context: {e}") from e
            except MCPServerError:
                raise
            except Exception:
                logger.exception("Unexpected error in list_errors")
                raise MCPServerError("Internal server error") from None

        self._tool_names.append("list_errors")

        @self._mcp.tool(description="Get system logs filtered by level")
        async def get_logs(
            ctx: dict[str, Any],
            level: str = "all",
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            try:
                session = SessionContext(**ctx)
                log_level = LogLevel(level)
                result = await impl.get_logs(session, level=log_level, limit=limit)
                return [e.model_dump(mode="json") for e in result]
            except ValidationError as e:
                raise SessionContextError(f"Invalid session context: {e}") from e
            except MCPServerError:
                raise
            except Exception:
                logger.exception("Unexpected error in get_logs")
                raise MCPServerError("Internal server error") from None

        self._tool_names.append("get_logs")

    # History tools

    def _register_history_tools(self) -> None:
        impl = self._impl

        @self._mcp.tool(description="List recent user actions in the system")
        async def list_user_actions(
            ctx: dict[str, Any],
            limit: int = 50,
        ) -> list[dict[str, Any]]:
            try:
                session = SessionContext(**ctx)
                result = await impl.list_user_actions(session, limit=limit)
                return [a.model_dump(mode="json") for a in result]
            except ValidationError as e:
                raise SessionContextError(f"Invalid session context: {e}") from e
            except MCPServerError:
                raise
            except Exception:
                logger.exception("Unexpected error in list_user_actions")
                raise MCPServerError("Internal server error") from None

        self._tool_names.append("list_user_actions")

    # Action tools

    def _register_action_tools(self) -> None:
        impl = self._impl

        @self._mcp.tool(
            description="List available actions, optionally filtered by component"
        )
        async def list_available_actions(
            ctx: dict[str, Any],
            component_id: str | None = None,
        ) -> list[dict[str, Any]]:
            try:
                session = SessionContext(**ctx)
                result = await impl.list_available_actions(
                    session, component_id=component_id
                )
                return [a.model_dump(mode="json") for a in result]
            except ValidationError as e:
                raise SessionContextError(f"Invalid session context: {e}") from e
            except MCPServerError:
                raise
            except Exception:
                logger.exception("Unexpected error in list_available_actions")
                raise MCPServerError("Internal server error") from None

        self._tool_names.append("list_available_actions")

        @self._mcp.tool(description="Execute an action in the system")
        async def execute_action(
            ctx: dict[str, Any],
            action_name: str,
            params: dict[str, Any],
        ) -> dict[str, Any]:
            try:
                session = SessionContext(**ctx)
                result = await impl.execute_action(session, action_name, params)
                return result.model_dump(mode="json")
            except ValidationError as e:
                raise SessionContextError(f"Invalid session context: {e}") from e
            except MCPServerError:
                raise
            except Exception:
                logger.exception("Unexpected error in execute_action")
                raise MCPServerError("Internal server error") from None

        self._tool_names.append("execute_action")

    # Meta tool

    def _register_capabilities_tool(self) -> None:
        caps = self._capabilities
        domain_tools = self._domain_tool_names
        name = self._name

        @self._mcp.tool(
            description="Get server capabilities and available tool categories"
        )
        async def get_capabilities() -> dict[str, Any]:
            return ServerCapabilities(
                system_name=name,
                capabilities=sorted(caps),
                domain_tools=sorted(domain_tools),
            ).model_dump(mode="json")

        self._tool_names.append("get_capabilities")

    # Domain tool decorator

    def domain_tool(self, **kwargs: Any) -> Callable:
        """Декоратор для регистрации доменно-специфичных инструментов."""
        inner = self._mcp.tool(**kwargs)

        def wrapper(fn: Callable) -> Callable:
            result = inner(fn)
            self._domain_tool_names.append(fn.__name__)
            self._tool_names.append(fn.__name__)
            return result

        return wrapper

    # Properties

    @property
    def capabilities(self) -> frozenset[str]:
        return frozenset(self._capabilities)

    @property
    def tool_names(self) -> list[str]:
        return list(self._tool_names)

    @property
    def mcp(self) -> FastMCP:
        return self._mcp

    # Run

    def run(self, transport: str = "streamable-http", **kwargs: Any) -> None:
        """Запуск MCP-сервера."""
        self._mcp.run(transport=transport, **kwargs)
