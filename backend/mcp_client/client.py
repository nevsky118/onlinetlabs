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


class _Connection:
    """One long-lived MCP session, owned by the task that opened it.

    The transport contexts are entered and exited inside `_run` only: anyio
    refuses a cancel scope exited from a different task, which is why a shared
    session cannot be held open with a plain AsyncExitStack.
    """

    def __init__(self, mcp_url: str, timeout: float):
        self._mcp_url = mcp_url
        self._timeout = timeout
        self._session: ClientSession | None = None
        self._ready = asyncio.Event()
        self._closing = asyncio.Event()
        self._failure: BaseException | None = None
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        """Holds the session open until closed, then tears it down here."""
        try:
            async with (
                streamablehttp_client(self._mcp_url, timeout=self._timeout) as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                self._session = session
                self._ready.set()
                await self._closing.wait()
        except BaseException as exc:
            self._failure = exc
            self._ready.set()
        finally:
            self._session = None

    async def session(self) -> ClientSession:
        """Waits for the session to come up, or raises what stopped it."""
        await self._ready.wait()
        if self._session is None:
            raise self._failure or ConnectionError("MCP session unavailable")
        return self._session

    @property
    def alive(self) -> bool:
        """False once the owning task has finished or failed."""
        return not self._task.done() and self._failure is None

    async def close(self) -> None:
        """Signals the owning task to unwind its contexts."""
        self._closing.set()
        try:
            await asyncio.wait_for(self._task, timeout=5.0)
        except (TimeoutError, asyncio.CancelledError, Exception):
            self._task.cancel()


class MCPClient:
    """Client to an MCP server via streamable HTTP transport.

    Implements StateProvider + ActionProvider + LogProvider + HistoryProvider.
    One session is held open and shared; a broken one is rebuilt on the next call.
    """

    def __init__(self, server_url: str, timeout: float = 30.0):
        self._server_url = server_url.rstrip("/")
        self._mcp_url = f"{self._server_url}/mcp"
        self._timeout = timeout
        self._connection: _Connection | None = None
        self._connect_lock = asyncio.Lock()

    async def _session(self) -> ClientSession:
        """Returns the shared session, opening or replacing it when needed."""
        connection = self._connection
        if connection is not None and connection.alive:
            return await connection.session()
        async with self._connect_lock:
            if self._connection is not None and self._connection.alive:
                return await self._connection.session()
            if self._connection is not None:
                await self._connection.close()
            self._connection = _Connection(self._mcp_url, self._timeout)
            return await self._connection.session()

    async def _drop_connection(self) -> None:
        """Discards the shared session so the next call reconnects."""
        async with self._connect_lock:
            connection, self._connection = self._connection, None
        if connection is not None:
            await connection.close()

    async def close(self) -> None:
        """Closes the shared session."""
        await self._drop_connection()

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
        try:
            session = await self._session()
            result = await session.call_tool(name, arguments)
        except MCPToolError:
            raise
        except Exception:
            # a broken stream must not be reused by the retry
            await self._drop_connection()
            raise

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
