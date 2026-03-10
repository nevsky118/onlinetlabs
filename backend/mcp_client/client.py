"""MCP-клиент для подключения к внешним MCP-серверам через streamable HTTP."""

import json
import logging
from datetime import datetime
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

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

logger = logging.getLogger(__name__)


class MCPClient:
    """Клиент к MCP-серверу через streamable HTTP transport.

    Реализует StateProvider + ActionProvider + LogProvider + HistoryProvider.
    Каждый вызов открывает сессию, вызывает tool, закрывает сессию.
    """

    def __init__(self, server_url: str, timeout: float = 30.0):
        self._server_url = server_url.rstrip("/")
        self._mcp_url = f"{self._server_url}/mcp"
        self._timeout = timeout

    def _ctx_dict(self, ctx: SessionContext) -> dict[str, Any]:
        """Сериализовать SessionContext в dict для MCP tool arguments."""
        return ctx.model_dump(exclude_none=True)

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Вызвать MCP tool и вернуть распарсенный результат."""
        result = None
        async with streamablehttp_client(self._mcp_url, timeout=self._timeout) as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)

        # Process result outside context managers to avoid ExceptionGroup wrapping
        if result is None:
            raise MCPToolError(name, "No result from MCP server")

        if result.isError:
            error_text = result.content[0].text if result.content else "Unknown error"
            raise MCPToolError(name, error_text)

        if result.structuredContent:
            return result.structuredContent

        if result.content:
            text = result.content[0].text
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return text

        return None

    # --- StateProvider ---

    async def list_components(self, ctx: SessionContext) -> list[Component]:
        data = await self._call_tool("list_components", {"ctx": self._ctx_dict(ctx)})
        items = data.get("result", data) if isinstance(data, dict) else data
        return [Component.model_validate(item) for item in items]

    async def get_component(
        self, ctx: SessionContext, component_id: str
    ) -> ComponentDetail:
        data = await self._call_tool(
            "get_component", {"ctx": self._ctx_dict(ctx), "component_id": component_id}
        )
        return ComponentDetail.model_validate(data)

    async def get_system_overview(self, ctx: SessionContext) -> SystemOverview:
        data = await self._call_tool("get_system_overview", {"ctx": self._ctx_dict(ctx)})
        return SystemOverview.model_validate(data)

    # --- ActionProvider ---

    async def list_available_actions(
        self, ctx: SessionContext, component_id: str | None = None
    ) -> list[ActionSpec]:
        args: dict[str, Any] = {"ctx": self._ctx_dict(ctx)}
        if component_id is not None:
            args["component_id"] = component_id
        data = await self._call_tool("list_available_actions", args)
        items = data.get("result", data) if isinstance(data, dict) else data
        return [ActionSpec.model_validate(item) for item in items]

    async def execute_action(
        self, ctx: SessionContext, action_name: str, params: dict[str, Any]
    ) -> ActionResult:
        data = await self._call_tool(
            "execute_action",
            {"ctx": self._ctx_dict(ctx), "action_name": action_name, "params": params},
        )
        return ActionResult.model_validate(data)

    # --- LogProvider ---

    async def list_errors(
        self, ctx: SessionContext, since: datetime | None = None
    ) -> list[ErrorEntry]:
        args: dict[str, Any] = {"ctx": self._ctx_dict(ctx)}
        if since is not None:
            args["since"] = since.isoformat()
        data = await self._call_tool("list_errors", args)
        items = data.get("result", data) if isinstance(data, dict) else data
        return [ErrorEntry.model_validate(item) for item in items]

    async def get_logs(
        self, ctx: SessionContext, level: LogLevel = LogLevel.ALL, limit: int = 100
    ) -> list[LogEntry]:
        data = await self._call_tool(
            "get_logs",
            {"ctx": self._ctx_dict(ctx), "level": level.value, "limit": limit},
        )
        items = data.get("result", data) if isinstance(data, dict) else data
        return [LogEntry.model_validate(item) for item in items]

    # --- HistoryProvider ---

    async def list_user_actions(
        self, ctx: SessionContext, limit: int = 50
    ) -> list[UserAction]:
        data = await self._call_tool(
            "list_user_actions", {"ctx": self._ctx_dict(ctx), "limit": limit}
        )
        items = data.get("result", data) if isinstance(data, dict) else data
        return [UserAction.model_validate(item) for item in items]

    # --- Domain tools (direct pass-through) ---

    async def call_domain_tool(
        self, tool_name: str, ctx: SessionContext, **kwargs: Any
    ) -> Any:
        """Вызвать произвольный domain tool (start_node, stop_node, etc.)."""
        args: dict[str, Any] = {"ctx": self._ctx_dict(ctx), **kwargs}
        return await self._call_tool(tool_name, args)


class MCPToolError(Exception):
    """Ошибка при вызове MCP tool."""

    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"MCP tool '{tool_name}' failed: {message}")
