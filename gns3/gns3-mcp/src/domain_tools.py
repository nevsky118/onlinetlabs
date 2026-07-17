# Registration of GNS3-specific domain tools.

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any, NamedTuple

import httpx
from mcp_sdk.context import SessionContext
from mcp_sdk.server import OnlinetlabsMCPServer

from src.api_client import GNS3ApiClient

_NO_DEFAULT = inspect.Parameter.empty


class _SimpleTool(NamedTuple):
    """Table-driven description of a uniform tool: session → api method → {success,message[,data]}."""

    name: str
    description: str
    api_method: str
    message: str  # .format(**kwargs), kwargs = named tool parameters
    has_data: bool
    params: tuple[tuple[str, type, Any], ...] = ()  # (name, type, default | _NO_DEFAULT)


_SIMPLE_TOOLS: tuple[_SimpleTool, ...] = (
    # -- Node lifecycle --
    _SimpleTool(
        "start_node",
        "Start a GNS3 node",
        "start_node",
        "Node {node_id} started",
        True,
        (("node_id", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "stop_node",
        "Stop a GNS3 node",
        "stop_node",
        "Node {node_id} stopped",
        True,
        (("node_id", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "reload_node",
        "Reload a GNS3 node",
        "reload_node",
        "Node {node_id} reloaded",
        True,
        (("node_id", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "suspend_node",
        "Suspend a GNS3 node",
        "suspend_node",
        "Node {node_id} suspended",
        True,
        (("node_id", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "isolate_node",
        "Isolate a node (suspend all links)",
        "isolate_node",
        "Node {node_id} isolated",
        True,
        (("node_id", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "unisolate_node",
        "Unisolate a node (resume all links)",
        "unisolate_node",
        "Node {node_id} unisolated",
        True,
        (("node_id", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "start_all_nodes",
        "Start all nodes in project",
        "start_all_nodes",
        "All nodes started",
        False,
    ),
    _SimpleTool(
        "stop_all_nodes", "Stop all nodes in project", "stop_all_nodes", "All nodes stopped", False
    ),
    # -- Links --
    _SimpleTool(
        "create_link",
        "Create a link between two nodes",
        "create_link",
        "Link created",
        True,
        (("nodes", list[dict], _NO_DEFAULT),),
    ),
    _SimpleTool(
        "delete_link",
        "Delete a link",
        "delete_link",
        "Link {link_id} deleted",
        False,
        (("link_id", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "start_capture",
        "Start packet capture on a link",
        "start_capture",
        "Capture started on {link_id}",
        True,
        (("link_id", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "stop_capture",
        "Stop packet capture on a link",
        "stop_capture",
        "Capture stopped on {link_id}",
        True,
        (("link_id", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "set_link_filter",
        "Set packet filter on a link (loss, delay)",
        "set_link_filter",
        "Filter set on {link_id}",
        True,
        (("link_id", str, _NO_DEFAULT), ("filters", dict, _NO_DEFAULT)),
    ),
    # -- Console --
    _SimpleTool(
        "reset_console",
        "Reset node console",
        "reset_console",
        "Console reset for {node_id}",
        False,
        (("node_id", str, _NO_DEFAULT),),
    ),
    # -- Templates --
    _SimpleTool(
        "create_node_from_template",
        "Create a node from template",
        "create_node_from_template",
        "Node created from template",
        True,
        (("template_id", str, _NO_DEFAULT), ("x", int, 0), ("y", int, 0)),
    ),
    # -- Project ops --
    _SimpleTool("open_project", "Open a GNS3 project", "open_project", "Project opened", True),
    _SimpleTool("close_project", "Close a GNS3 project", "close_project", "Project closed", True),
    _SimpleTool(
        "lock_project", "Lock project to prevent changes", "lock_project", "Project locked", True
    ),
    _SimpleTool("unlock_project", "Unlock project", "unlock_project", "Project unlocked", True),
    _SimpleTool(
        "duplicate_project", "Duplicate project", "duplicate_project", "Project duplicated", True
    ),
    # -- Snapshots --
    _SimpleTool(
        "create_snapshot",
        "Create project snapshot",
        "create_snapshot",
        "Snapshot '{name}' created",
        True,
        (("name", str, _NO_DEFAULT),),
    ),
    _SimpleTool(
        "restore_snapshot",
        "Restore project snapshot",
        "restore_snapshot",
        "Snapshot {snapshot_id} restored",
        True,
        (("snapshot_id", str, _NO_DEFAULT),),
    ),
)


def _build_simple_tool(
    spec: _SimpleTool,
    get_client: Callable[[SessionContext], Awaitable[GNS3ApiClient]],
    get_project_id: Callable[[SessionContext], str],
) -> Callable:
    """Builds a closure from the table-driven spec + sets a real signature for the MCP schema."""

    async def tool(ctx: dict[str, Any], **kwargs: Any) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        method = getattr(client, spec.api_method)
        result = await method(
            get_project_id(session), *(kwargs[p_name] for p_name, _, _ in spec.params)
        )
        message = spec.message.format(**kwargs)
        if spec.has_data:
            return {"success": True, "message": message, "data": result}
        return {"success": True, "message": message}

    tool.__name__ = spec.name
    tool.__signature__ = inspect.Signature(
        parameters=[
            inspect.Parameter(
                "ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=dict[str, Any]
            ),
            *(
                inspect.Parameter(
                    p_name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=p_type,
                    default=p_default,
                )
                for p_name, p_type, p_default in spec.params
            ),
        ],
        return_annotation=dict,
    )
    return tool


def register_domain_tools(
    server: OnlinetlabsMCPServer,
    get_client: Callable[[SessionContext], Awaitable[GNS3ApiClient]],
    get_project_id: Callable[[SessionContext], str],
    service_url: str | None = None,
) -> None:
    """Registers all GNS3 domain tools.

    get_client(ctx) -> GNS3ApiClient
    get_project_id(ctx) -> str
    service_url — base URL of gns3-service for exec/console-read (None → tool returns an error).
    """

    for spec in _SIMPLE_TOOLS:
        server.domain_tool(description=spec.description)(
            _build_simple_tool(spec, get_client, get_project_id)
        )

    # -- Outliers: don't fit the uniform shape, left explicit --

    @server.domain_tool(
        description="Execute a vtysh command on a node console via gns3-service "
        "(observe device state through MCP instead of a telnet bypass)"
    )
    async def exec_vtysh(ctx: dict[str, Any], node_id: str, command: str) -> dict:
        session = SessionContext(**ctx)
        if not service_url:
            return {
                "success": False,
                "message": "gns3-service URL not configured",
                "data": None,
            }
        payload = {
            "project_id": get_project_id(session),
            "node_id": node_id,
            "command": command,
        }
        async with httpx.AsyncClient(base_url=service_url, timeout=30) as client:
            resp = await client.post("/v1/exec/vtysh", json=payload)
        if resp.status_code != 200:
            return {
                "success": False,
                "message": f"exec failed: HTTP {resp.status_code}",
                "data": None,
            }
        return {"success": True, "message": "exec ok", "data": resp.json()}

    @server.domain_tool(description="Get console connection info for a node")
    async def get_console_info(ctx: dict[str, Any], node_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        node = await client.get_node(get_project_id(session), node_id)
        return {
            "node_id": node_id,
            "console": node.get("console"),
            "console_type": node.get("console_type"),
            "console_host": node.get("console_host"),
        }

    @server.domain_tool(description="List available node templates")
    async def list_templates(ctx: dict[str, Any]) -> list[dict]:
        session = SessionContext(**ctx)
        client = await get_client(session)
        return await client.list_templates()

    @server.domain_tool(description="List project snapshots")
    async def list_snapshots(ctx: dict[str, Any]) -> list[dict]:
        session = SessionContext(**ctx)
        client = await get_client(session)
        return await client.list_snapshots(get_project_id(session))
