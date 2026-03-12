# GNS3Server — реализация SDK протоколов.

from __future__ import annotations

from datetime import datetime

import httpx
from mcp_sdk.context import SessionContext
from mcp_sdk.errors import (
    ActionExecutionError,
    ComponentNotFoundError,
    TargetSystemAPIError,
)
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

from src.api_client import GNS3ApiClient
from src.log_buffer import LogBuffer
from src.mappers import (
    build_system_overview,
    link_to_component,
    link_to_component_detail,
    node_to_component,
    node_to_component_detail,
)

if __import__("typing").TYPE_CHECKING:
    from mcp_sdk.connection import ConnectionPool


ACTIONS: list[dict] = [
    {"name": "start_all_nodes", "description": "Запуск всех нод", "params": {}, "types": []},
    {"name": "stop_all_nodes", "description": "Остановка всех нод", "params": {}, "types": []},
    {"name": "start_node", "description": "Запуск ноды", "params": {"node_id": {"type": "string"}}, "types": ["vpcs", "qemu", "dynamips", "docker"]},
    {"name": "stop_node", "description": "Остановка ноды", "params": {"node_id": {"type": "string"}}, "types": ["vpcs", "qemu", "dynamips", "docker"]},
    {"name": "reload_node", "description": "Перезагрузка ноды", "params": {"node_id": {"type": "string"}}, "types": ["vpcs", "qemu", "dynamips", "docker"]},
    {"name": "suspend_node", "description": "Приостановка ноды", "params": {"node_id": {"type": "string"}}, "types": ["vpcs", "qemu", "dynamips", "docker"]},
    {"name": "isolate_node", "description": "Отключить все линки ноды", "params": {"node_id": {"type": "string"}}, "types": ["vpcs", "qemu", "dynamips", "docker"]},
    {"name": "unisolate_node", "description": "Восстановить линки ноды", "params": {"node_id": {"type": "string"}}, "types": ["vpcs", "qemu", "dynamips", "docker"]},
    {"name": "create_link", "description": "Создать соединение", "params": {"nodes": {"type": "array"}}, "types": ["link"]},
    {"name": "delete_link", "description": "Удалить соединение", "params": {"link_id": {"type": "string"}}, "types": ["link"]},
    {"name": "start_capture", "description": "Начать захват пакетов", "params": {"link_id": {"type": "string"}}, "types": ["link"]},
    {"name": "stop_capture", "description": "Остановить захват", "params": {"link_id": {"type": "string"}}, "types": ["link"]},
    {"name": "set_link_filter", "description": "Установить фильтры", "params": {"link_id": {"type": "string"}, "filters": {"type": "object"}}, "types": ["link"]},
    {"name": "open_project", "description": "Открыть проект", "params": {}, "types": []},
    {"name": "close_project", "description": "Закрыть проект", "params": {}, "types": []},
    {"name": "create_snapshot", "description": "Сохранить состояние", "params": {"name": {"type": "string"}}, "types": []},
    {"name": "restore_snapshot", "description": "Восстановить состояние", "params": {"snapshot_id": {"type": "string"}}, "types": []},
]


class GNS3Server:
    """Реализация SDK протоколов для GNS3.

    Получает api_client извне (из ConnectionPool или напрямую).
    При наличии pool — резолвит клиент per-session через pool.
    """

    def __init__(
        self,
        api_client: GNS3ApiClient | None = None,
        log_buffer: "LogBuffer | None" = None,
        history_url: str | None = None,
        pool: "ConnectionPool | None" = None,
    ) -> None:
        self._api = api_client
        self._pool = pool
        self._log_buffer = log_buffer
        self._history_url = history_url  # gns3-service base URL

    async def _resolve_api(self, ctx: SessionContext) -> GNS3ApiClient:
        """Возвращает api_client: прямой или из пула."""
        if self._api is not None:
            return self._api
        if self._pool is not None:
            return await self._pool.get_connection(ctx)
        from mcp_sdk.errors import SessionContextError
        raise SessionContextError("No api_client or pool configured")

    def _project_id(self, ctx: SessionContext) -> str:
        """Извлекает project_id из контекста."""
        if not ctx.project_id:
            from mcp_sdk.errors import SessionContextError

            raise SessionContextError("project_id is required in SessionContext")
        return ctx.project_id

    # -- StateProvider --

    async def list_components(self, ctx: SessionContext) -> list[Component]:
        pid = self._project_id(ctx)
        api = await self._resolve_api(ctx)
        nodes = await api.list_nodes(pid)
        links = await api.list_links(pid)

        node_names = {node["node_id"]: node["name"] for node in nodes}

        components: list[Component] = []
        for node in nodes:
            components.append(node_to_component(node))
        for link in links:
            components.append(link_to_component(link, node_names))
        return components

    async def get_component(
        self, ctx: SessionContext, component_id: str
    ) -> ComponentDetail:
        pid = self._project_id(ctx)

        api = await self._resolve_api(ctx)

        # Пробуем как ноду
        try:
            node = await api.get_node(pid, component_id)
            links = await api.list_links(pid)
            peer_ids = []
            for link in links:
                link_node_ids = [node["node_id"] for node in link["nodes"]]
                if component_id in link_node_ids:
                    peer_ids.extend(
                        nid for nid in link_node_ids if nid != component_id
                    )
            return node_to_component_detail(node, peer_ids)
        except TargetSystemAPIError:
            pass

        # Пробуем как линк
        links = await api.list_links(pid)
        nodes = await api.list_nodes(pid)
        node_names = {node["node_id"]: node["name"] for node in nodes}
        for link in links:
            if link["link_id"] == component_id:
                return link_to_component_detail(link, node_names)

        raise ComponentNotFoundError(component_id=component_id)

    async def get_system_overview(self, ctx: SessionContext) -> SystemOverview:
        pid = self._project_id(ctx)
        api = await self._resolve_api(ctx)
        nodes = await api.list_nodes(pid)
        links = await api.list_links(pid)
        version = await api.get_version()
        project = await api.get_project(pid)
        return build_system_overview(nodes, links, version, project.get("name", pid))

    # -- LogProvider --

    async def list_errors(self, ctx: SessionContext, since: datetime | None = None) -> list[ErrorEntry]:
        """Ошибки из ring buffer."""
        await self._ensure_log_buffer(ctx)
        return self._log_buffer.get_errors(since=since)

    async def get_logs(self, ctx: SessionContext, level: LogLevel = LogLevel.ALL, limit: int = 100) -> list[LogEntry]:
        """Логи из ring buffer с фильтрацией."""
        await self._ensure_log_buffer(ctx)
        return self._log_buffer.get_logs(level=level, limit=limit)

    async def _ensure_log_buffer(self, ctx: SessionContext) -> None:
        """Ленивая инициализация LogBuffer + WS подключение."""
        if self._log_buffer is None:
            from src.log_buffer import LogBuffer
            self._log_buffer = LogBuffer()

        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(ctx.environment_url.rstrip("/"))
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        pid = self._project_id(ctx)
        ws_url = urlunparse((ws_scheme, parsed.netloc, f"/v3/projects/{pid}/notifications/ws", "", "", ""))
        jwt = ctx.metadata.get("gns3_jwt") if ctx.metadata else None
        await self._log_buffer.ensure_connected(ws_url, jwt)

    # -- ActionProvider --

    async def list_available_actions(self, ctx: SessionContext, component_id: str | None = None) -> list[ActionSpec]:
        if component_id:
            # Определяем тип компонента
            try:
                detail = await self.get_component(ctx, component_id)
                comp_type = detail.type
            except Exception:
                comp_type = None
            return [
                ActionSpec(name=action["name"], description=action["description"], parameters=action["params"], component_types=action["types"])
                for action in ACTIONS
                if not action["types"] or (comp_type and comp_type in action["types"])
            ]
        return [
            ActionSpec(name=action["name"], description=action["description"], parameters=action["params"], component_types=action["types"])
            for action in ACTIONS
        ]

    async def execute_action(self, ctx: SessionContext, action_name: str, params: dict) -> ActionResult:
        pid = self._project_id(ctx)
        api = await self._resolve_api(ctx)
        try:
            match action_name:
                case "start_node":
                    await api.start_node(pid, params["node_id"])
                case "stop_node":
                    await api.stop_node(pid, params["node_id"])
                case "reload_node":
                    await api.reload_node(pid, params["node_id"])
                case "suspend_node":
                    await api.suspend_node(pid, params["node_id"])
                case "isolate_node":
                    await api.isolate_node(pid, params["node_id"])
                case "unisolate_node":
                    await api.unisolate_node(pid, params["node_id"])
                case "start_all_nodes":
                    await api.start_all_nodes(pid)
                case "stop_all_nodes":
                    await api.stop_all_nodes(pid)
                case "create_link":
                    await api.create_link(pid, params["nodes"])
                case "delete_link":
                    await api.delete_link(pid, params["link_id"])
                case "start_capture":
                    await api.start_capture(pid, params["link_id"])
                case "stop_capture":
                    await api.stop_capture(pid, params["link_id"])
                case "set_link_filter":
                    await api.set_link_filter(pid, params["link_id"], params["filters"])
                case "open_project":
                    await api.open_project(pid)
                case "close_project":
                    await api.close_project(pid)
                case "create_snapshot":
                    await api.create_snapshot(pid, params["name"])
                case "restore_snapshot":
                    await api.restore_snapshot(pid, params["snapshot_id"])
                case _:
                    raise ActionExecutionError(action_name, f"Unknown action: {action_name}")
            return ActionResult(success=True, message=f"Action '{action_name}' executed successfully")
        except ActionExecutionError:
            raise
        except KeyError as exc:
            raise ActionExecutionError(action_name, f"Missing parameter: {exc}") from exc
        except Exception as exc:
            raise ActionExecutionError(action_name, str(exc)) from exc

    # -- HistoryProvider --

    async def list_user_actions(self, ctx: SessionContext, limit: int = 50) -> list[UserAction]:
        """Запрашивает историю из gns3-service."""
        if not self._history_url:
            return []
        async with httpx.AsyncClient(base_url=self._history_url) as client:
            response = await client.get(
                f"/history/{ctx.session_id}/actions",
                params={"limit": limit},
            )
            if response.status_code != 200:
                return []
            events = response.json()
            return [
                UserAction(
                    timestamp=event["timestamp"],
                    component_id=event.get("component_id"),
                    action=event["event_type"],
                    raw_command=None,
                    success=True,
                )
                for event in events
            ]
