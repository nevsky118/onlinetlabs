"""MCP client for connecting to external MCP servers via streamable HTTP."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp_sdk.context import SessionContext
from mcp_sdk.models import (
    ActionResult,
    Component,
    ComponentDetail,
    ErrorEntry,
    LogEntry,
    LogLevel,
    UserAction,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class MCPClient:
    """Client to an MCP server via streamable HTTP transport.

    Implements StateProvider + ActionProvider + LogProvider + HistoryProvider.
    Each call opens a session, calls the tool, closes the session.
    """

    def __init__(self, server_url: str, timeout: float = 30.0):
        self._server_url = server_url.rstrip("/")
        self._mcp_url = f"{self._server_url}/mcp"
        self._timeout = timeout

    def _ctx_dict(self, ctx: SessionContext) -> dict[str, Any]:
        """Serialize SessionContext into a dict for MCP tool arguments."""
        return ctx.model_dump(exclude_none=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.3, max=2.0),
        retry=retry_if_exception_type(
            (httpx.RequestError, ConnectionError, asyncio.TimeoutError, OSError)
        ),
        reraise=True,
    )
    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool and return the parsed result.

        Transient network failures are retried three times with exponential backoff.
        MCPToolError (tool-level logical errors) is not retried, to avoid masking a bug.
        """
        result = None
        async with (
            streamablehttp_client(self._mcp_url, timeout=self._timeout) as (
                read,
                write,
                _,
            ),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            result = await session.call_tool(name, arguments)

        # Parse the result outside the async with, otherwise MCP wraps exceptions
        # in an ExceptionGroup and we lose the original traceback.
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

    # StateProvider (topology state)

    async def list_components(self, ctx: SessionContext) -> list[Component]:
        """Get the list of topology components from the MCP server."""
        data = await self._call_tool("list_components", {"ctx": self._ctx_dict(ctx)})
        items = data.get("result", data) if isinstance(data, dict) else data
        return [Component.model_validate(item) for item in items]

    async def get_component(self, ctx: SessionContext, component_id: str) -> ComponentDetail:
        """Get a component's detailed state by its id."""
        data = await self._call_tool(
            "get_component", {"ctx": self._ctx_dict(ctx), "component_id": component_id}
        )
        return ComponentDetail.model_validate(data)

    # ActionProvider (actions on nodes)

    async def execute_action(
        self, ctx: SessionContext, action_name: str, params: dict[str, Any]
    ) -> ActionResult:
        """Execute an action on a node via the MCP ActionProvider."""
        data = await self._call_tool(
            "execute_action",
            {"ctx": self._ctx_dict(ctx), "action_name": action_name, "params": params},
        )
        return ActionResult.model_validate(data)

    # LogProvider (logs and errors)

    async def list_errors(
        self, ctx: SessionContext, since: datetime | None = None
    ) -> list[ErrorEntry]:
        """Get environment errors, optionally since a given timestamp."""
        args: dict[str, Any] = {"ctx": self._ctx_dict(ctx)}
        if since is not None:
            args["since"] = since.isoformat()
        data = await self._call_tool("list_errors", args)
        items = data.get("result", data) if isinstance(data, dict) else data
        return [ErrorEntry.model_validate(item) for item in items]

    async def get_logs(
        self, ctx: SessionContext, level: LogLevel = LogLevel.ALL, limit: int = 100
    ) -> list[LogEntry]:
        """Get environment logs filtered by level."""
        data = await self._call_tool(
            "get_logs",
            {"ctx": self._ctx_dict(ctx), "level": level.value, "limit": limit},
        )
        items = data.get("result", data) if isinstance(data, dict) else data
        return [LogEntry.model_validate(item) for item in items]

    # HistoryProvider (user actions)

    async def list_user_actions(self, ctx: SessionContext, limit: int = 50) -> list[UserAction]:
        """Get the history of user actions in the environment."""
        data = await self._call_tool(
            "list_user_actions", {"ctx": self._ctx_dict(ctx), "limit": limit}
        )
        items = data.get("result", data) if isinstance(data, dict) else data
        return [UserAction.model_validate(item) for item in items]

    # Domain tools (direct pass-through)


class MCPToolError(Exception):
    """Error raised when calling an MCP tool."""

    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"MCP tool '{tool_name}' failed: {message}")
