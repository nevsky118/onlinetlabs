"""MCP-клиент для подключения к внешним MCP-серверам через streamable HTTP."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

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

logger = logging.getLogger(__name__)


class MCPClient:
    """Клиент к MCP-серверу через streamable HTTP transport.

    Реализует StateProvider + ActionProvider + LogProvider + HistoryProvider.
    Каждый вызов открывает сессию, вызывает tool, закрывает сессию.
    """

    def __init__(self, server_url: str, timeout: float = 30.0):
        """Сохраняет URL MCP-сервера и таймаут вызовов."""
        self._server_url = server_url.rstrip("/")
        self._mcp_url = f"{self._server_url}/mcp"
        self._timeout = timeout

    def _ctx_dict(self, ctx: SessionContext) -> dict[str, Any]:
        """Сериализовать SessionContext в dict для MCP tool arguments."""
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
        """Вызвать MCP tool и вернуть распарсенный результат.

        Транзитные сетевые сбои ретраятся три раза с экспоненциальной паузой.
        MCPToolError (логические ошибки tool) не ретраим, чтобы не маскировать баг.
        """
        result = None
        async with streamablehttp_client(self._mcp_url, timeout=self._timeout) as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)

        # Парсим результат вне async with, иначе MCP оборачивает исключения в
        # ExceptionGroup и теряем оригинальный traceback.
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

    # StateProvider — состояние топологии

    async def list_components(self, ctx: SessionContext) -> list[Component]:
        """Получить список компонентов топологии из MCP-сервера."""
        data = await self._call_tool("list_components", {"ctx": self._ctx_dict(ctx)})
        items = data.get("result", data) if isinstance(data, dict) else data
        return [Component.model_validate(item) for item in items]

    async def get_component(
        self, ctx: SessionContext, component_id: str
    ) -> ComponentDetail:
        """Получить детальное состояние компонента по его id."""
        data = await self._call_tool(
            "get_component", {"ctx": self._ctx_dict(ctx), "component_id": component_id}
        )
        return ComponentDetail.model_validate(data)

    # ActionProvider — действия над узлами

    async def execute_action(
        self, ctx: SessionContext, action_name: str, params: dict[str, Any]
    ) -> ActionResult:
        """Выполнить действие над узлом через MCP ActionProvider."""
        data = await self._call_tool(
            "execute_action",
            {"ctx": self._ctx_dict(ctx), "action_name": action_name, "params": params},
        )
        return ActionResult.model_validate(data)

    # LogProvider — логи и ошибки

    async def list_errors(
        self, ctx: SessionContext, since: datetime | None = None
    ) -> list[ErrorEntry]:
        """Получить ошибки среды, опционально начиная с момента since."""
        args: dict[str, Any] = {"ctx": self._ctx_dict(ctx)}
        if since is not None:
            args["since"] = since.isoformat()
        data = await self._call_tool("list_errors", args)
        items = data.get("result", data) if isinstance(data, dict) else data
        return [ErrorEntry.model_validate(item) for item in items]

    async def get_logs(
        self, ctx: SessionContext, level: LogLevel = LogLevel.ALL, limit: int = 100
    ) -> list[LogEntry]:
        """Получить логи среды отфильтрованные по уровню."""
        data = await self._call_tool(
            "get_logs",
            {"ctx": self._ctx_dict(ctx), "level": level.value, "limit": limit},
        )
        items = data.get("result", data) if isinstance(data, dict) else data
        return [LogEntry.model_validate(item) for item in items]

    # HistoryProvider — пользовательские действия

    async def list_user_actions(
        self, ctx: SessionContext, limit: int = 50
    ) -> list[UserAction]:
        """Получить историю действий пользователя в среде."""
        data = await self._call_tool(
            "list_user_actions", {"ctx": self._ctx_dict(ctx), "limit": limit}
        )
        items = data.get("result", data) if isinstance(data, dict) else data
        return [UserAction.model_validate(item) for item in items]

    # Domain-тулзы (прямой проброс)

    async def call_domain_tool(
        self, tool_name: str, ctx: SessionContext, **kwargs: Any
    ) -> Any:
        """Вызвать произвольный domain tool (start_node, stop_node, etc.)."""
        args: dict[str, Any] = {"ctx": self._ctx_dict(ctx), **kwargs}
        return await self._call_tool(tool_name, args)


class MCPToolError(Exception):
    """Ошибка при вызове MCP tool."""

    def __init__(self, tool_name: str, message: str):
        """Сохраняет имя tool и формирует сообщение об ошибке."""
        self.tool_name = tool_name
        super().__init__(f"MCP tool '{tool_name}' failed: {message}")
