# Регистрация GNS3-специфичных domain tools.

from __future__ import annotations

from typing import Any

from onlinetlabs_mcp_sdk.context import SessionContext
from onlinetlabs_mcp_sdk.server import OnlinetlabsMCPServer

from src.api_client import GNS3ApiClient


def register_domain_tools(
    server: OnlinetlabsMCPServer,
    get_client: Any,
    get_project_id: Any,
) -> None:
    """Регистрирует все GNS3 domain tools.

    get_client(ctx) -> GNS3ApiClient
    get_project_id(ctx) -> str
    """

    # -- Node lifecycle --

    @server.domain_tool(description="Start a GNS3 node")
    async def start_node(ctx: dict[str, Any], node_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.start_node(get_project_id(session), node_id)
        return {"success": True, "message": f"Node {node_id} started", "data": result}

    @server.domain_tool(description="Stop a GNS3 node")
    async def stop_node(ctx: dict[str, Any], node_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.stop_node(get_project_id(session), node_id)
        return {"success": True, "message": f"Node {node_id} stopped", "data": result}

    @server.domain_tool(description="Reload a GNS3 node")
    async def reload_node(ctx: dict[str, Any], node_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.reload_node(get_project_id(session), node_id)
        return {"success": True, "message": f"Node {node_id} reloaded", "data": result}

    @server.domain_tool(description="Suspend a GNS3 node")
    async def suspend_node(ctx: dict[str, Any], node_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.suspend_node(get_project_id(session), node_id)
        return {"success": True, "message": f"Node {node_id} suspended", "data": result}

    @server.domain_tool(description="Isolate a node (suspend all links)")
    async def isolate_node(ctx: dict[str, Any], node_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.isolate_node(get_project_id(session), node_id)
        return {"success": True, "message": f"Node {node_id} isolated", "data": result}

    @server.domain_tool(description="Unisolate a node (resume all links)")
    async def unisolate_node(ctx: dict[str, Any], node_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.unisolate_node(get_project_id(session), node_id)
        return {"success": True, "message": f"Node {node_id} unisolated", "data": result}

    @server.domain_tool(description="Start all nodes in project")
    async def start_all_nodes(ctx: dict[str, Any]) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        await client.start_all_nodes(get_project_id(session))
        return {"success": True, "message": "All nodes started"}

    @server.domain_tool(description="Stop all nodes in project")
    async def stop_all_nodes(ctx: dict[str, Any]) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        await client.stop_all_nodes(get_project_id(session))
        return {"success": True, "message": "All nodes stopped"}

    # -- Links --

    @server.domain_tool(description="Create a link between two nodes")
    async def create_link(ctx: dict[str, Any], nodes: list[dict]) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.create_link(get_project_id(session), nodes)
        return {"success": True, "message": "Link created", "data": result}

    @server.domain_tool(description="Delete a link")
    async def delete_link(ctx: dict[str, Any], link_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        await client.delete_link(get_project_id(session), link_id)
        return {"success": True, "message": f"Link {link_id} deleted"}

    @server.domain_tool(description="Start packet capture on a link")
    async def start_capture(ctx: dict[str, Any], link_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.start_capture(get_project_id(session), link_id)
        return {"success": True, "message": f"Capture started on {link_id}", "data": result}

    @server.domain_tool(description="Stop packet capture on a link")
    async def stop_capture(ctx: dict[str, Any], link_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.stop_capture(get_project_id(session), link_id)
        return {"success": True, "message": f"Capture stopped on {link_id}", "data": result}

    @server.domain_tool(description="Set packet filter on a link (loss, delay)")
    async def set_link_filter(ctx: dict[str, Any], link_id: str, filters: dict) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.set_link_filter(get_project_id(session), link_id, filters)
        return {"success": True, "message": f"Filter set on {link_id}", "data": result}

    # -- Console --

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

    @server.domain_tool(description="Reset node console")
    async def reset_console(ctx: dict[str, Any], node_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        await client.reset_console(get_project_id(session), node_id)
        return {"success": True, "message": f"Console reset for {node_id}"}

    # -- Templates --

    @server.domain_tool(description="List available node templates")
    async def list_templates(ctx: dict[str, Any]) -> list[dict]:
        session = SessionContext(**ctx)
        client = await get_client(session)
        return await client.list_templates()

    @server.domain_tool(description="Create a node from template")
    async def create_node_from_template(ctx: dict[str, Any], template_id: str, x: int = 0, y: int = 0) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.create_node_from_template(get_project_id(session), template_id, x, y)
        return {"success": True, "message": "Node created from template", "data": result}

    # -- Project ops --

    @server.domain_tool(description="Open a GNS3 project")
    async def open_project(ctx: dict[str, Any]) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.open_project(get_project_id(session))
        return {"success": True, "message": "Project opened", "data": result}

    @server.domain_tool(description="Close a GNS3 project")
    async def close_project(ctx: dict[str, Any]) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.close_project(get_project_id(session))
        return {"success": True, "message": "Project closed", "data": result}

    @server.domain_tool(description="Lock project to prevent changes")
    async def lock_project(ctx: dict[str, Any]) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.lock_project(get_project_id(session))
        return {"success": True, "message": "Project locked", "data": result}

    @server.domain_tool(description="Unlock project")
    async def unlock_project(ctx: dict[str, Any]) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.unlock_project(get_project_id(session))
        return {"success": True, "message": "Project unlocked", "data": result}

    @server.domain_tool(description="Duplicate project")
    async def duplicate_project(ctx: dict[str, Any]) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.duplicate_project(get_project_id(session))
        return {"success": True, "message": "Project duplicated", "data": result}

    # -- Snapshots --

    @server.domain_tool(description="List project snapshots")
    async def list_snapshots(ctx: dict[str, Any]) -> list[dict]:
        session = SessionContext(**ctx)
        client = await get_client(session)
        return await client.list_snapshots(get_project_id(session))

    @server.domain_tool(description="Create project snapshot")
    async def create_snapshot(ctx: dict[str, Any], name: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.create_snapshot(get_project_id(session), name)
        return {"success": True, "message": f"Snapshot '{name}' created", "data": result}

    @server.domain_tool(description="Restore project snapshot")
    async def restore_snapshot(ctx: dict[str, Any], snapshot_id: str) -> dict:
        session = SessionContext(**ctx)
        client = await get_client(session)
        result = await client.restore_snapshot(get_project_id(session), snapshot_id)
        return {"success": True, "message": f"Snapshot {snapshot_id} restored", "data": result}
