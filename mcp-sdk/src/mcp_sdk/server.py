"""MCP server builder with automatic protocol discovery."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any

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


def _tool_errors(name: str) -> Callable:
    """Unified exception mapping for tool functions: SessionContext/domain/unexpected."""

    def deco(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await fn(*args, **kwargs)
            except ValidationError as e:
                raise SessionContextError(f"Invalid session context: {e}") from e
            except MCPServerError:
                raise
            except Exception:
                logger.exception("Unexpected error in %s", name)
                raise MCPServerError("Internal server error") from None

        return wrapper

    return deco


class OnlinetlabsMCPServer:
    """Wrapper over FastMCP with protocol auto-discovery and tool registration."""

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
        """The implementation must at minimum satisfy StateProvider."""
        if not isinstance(self._impl, StateProvider):
            raise ValueError(
                f"Implementation must satisfy StateProvider protocol. "
                f"Got {type(self._impl).__name__}"
            )

    # Discovery & registration

    def _discover_and_register(self) -> None:
        """Introspect protocols and register the corresponding MCP tools."""
        # StateProvider — always (checked in _validate_minimum)
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

        # Meta tool — always
        self._register_capabilities_tool()

    # State tools

    def _register_state_tools(self) -> None:
        impl = self._impl

        @self._mcp.tool(description="List all components in the system")
        @_tool_errors("list_components")
        async def list_components(ctx: dict[str, Any]) -> list[dict[str, Any]]:
            session = SessionContext(**ctx)
            result = await impl.list_components(session)
            return [c.model_dump(mode="json") for c in result]

        self._tool_names.append("list_components")

        @self._mcp.tool(description="Get detailed information about a specific component")
        @_tool_errors("get_component")
        async def get_component(ctx: dict[str, Any], component_id: str) -> dict[str, Any]:
            session = SessionContext(**ctx)
            result = await impl.get_component(session, component_id)
            return result.model_dump(mode="json")

        self._tool_names.append("get_component")

        @self._mcp.tool(description="Get a high-level overview of the entire system")
        @_tool_errors("get_system_overview")
        async def get_system_overview(ctx: dict[str, Any]) -> dict[str, Any]:
            session = SessionContext(**ctx)
            result = await impl.get_system_overview(session)
            return result.model_dump(mode="json")

        self._tool_names.append("get_system_overview")

    # Log tools

    def _register_log_tools(self) -> None:
        impl = self._impl

        @self._mcp.tool(description="List recent errors and warnings")
        @_tool_errors("list_errors")
        async def list_errors(
            ctx: dict[str, Any],
            since: str | None = None,
        ) -> list[dict[str, Any]]:
            session = SessionContext(**ctx)
            try:
                since_dt = datetime.fromisoformat(since) if since else None
            except ValueError as e:
                raise SessionContextError(f"Invalid since timestamp: {since}") from e
            result = await impl.list_errors(session, since=since_dt)
            return [e.model_dump(mode="json") for e in result]

        self._tool_names.append("list_errors")

        @self._mcp.tool(description="Get system logs filtered by level")
        @_tool_errors("get_logs")
        async def get_logs(
            ctx: dict[str, Any],
            level: str = "all",
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            session = SessionContext(**ctx)
            try:
                log_level = LogLevel(level)
            except ValueError as e:
                raise SessionContextError(f"Invalid log level: {level}") from e
            result = await impl.get_logs(session, level=log_level, limit=limit)
            return [e.model_dump(mode="json") for e in result]

        self._tool_names.append("get_logs")

    # History tools

    def _register_history_tools(self) -> None:
        impl = self._impl

        @self._mcp.tool(description="List recent user actions in the system")
        @_tool_errors("list_user_actions")
        async def list_user_actions(
            ctx: dict[str, Any],
            limit: int = 50,
        ) -> list[dict[str, Any]]:
            session = SessionContext(**ctx)
            result = await impl.list_user_actions(session, limit=limit)
            return [a.model_dump(mode="json") for a in result]

        self._tool_names.append("list_user_actions")

    # Action tools

    def _register_action_tools(self) -> None:
        impl = self._impl

        @self._mcp.tool(description="List available actions, optionally filtered by component")
        @_tool_errors("list_available_actions")
        async def list_available_actions(
            ctx: dict[str, Any],
            component_id: str | None = None,
        ) -> list[dict[str, Any]]:
            session = SessionContext(**ctx)
            result = await impl.list_available_actions(session, component_id=component_id)
            return [a.model_dump(mode="json") for a in result]

        self._tool_names.append("list_available_actions")

        @self._mcp.tool(description="Execute an action in the system")
        @_tool_errors("execute_action")
        async def execute_action(
            ctx: dict[str, Any],
            action_name: str,
            params: dict[str, Any],
        ) -> dict[str, Any]:
            session = SessionContext(**ctx)
            result = await impl.execute_action(session, action_name, params)
            return result.model_dump(mode="json")

        self._tool_names.append("execute_action")

    # Meta tool

    def _register_capabilities_tool(self) -> None:
        caps = self._capabilities
        domain_tools = self._domain_tool_names
        name = self._name

        @self._mcp.tool(description="Get server capabilities and available tool categories")
        async def get_capabilities() -> dict[str, Any]:
            return ServerCapabilities(
                system_name=name,
                capabilities=sorted(caps),
                domain_tools=sorted(domain_tools),
            ).model_dump(mode="json")

        self._tool_names.append("get_capabilities")

    # Domain tool decorator

    def domain_tool(self, **kwargs: Any) -> Callable:
        """Decorator for registering domain-specific tools."""
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
        """Run the MCP server."""
        self._mcp.run(transport=transport, **kwargs)
