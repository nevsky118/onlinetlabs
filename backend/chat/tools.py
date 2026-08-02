"""MCP tools available to the chat LLM."""

import asyncio
import json
from urllib.parse import urlparse

from i18n import Locale, t

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_components",
            "description": "List of components (nodes and links) in the current lab environment and their status.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_component",
            "description": "Detailed state of a single component by id.",
            "parameters": {
                "type": "object",
                "properties": {"component_id": {"type": "string"}},
                "required": ["component_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_vpcs_ip",
            "description": (
                "Run 'show ip' on a VPCS node and return its current IP address and gateway. "
                "Use this to check whether the student configured the correct IP."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {
                        "type": "string",
                        "description": "Node name, for example PC1 or PC2",
                    }
                },
                "required": ["node_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_errors",
            "description": "Recent environment errors.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

ALLOWED_TOOLS = {t["function"]["name"] for t in TOOL_DEFINITIONS}


async def run_vpcs_show_ip(node_name: str, ctx, mcp_client, locale: Locale) -> dict:
    """Connects via telnet to the VPCS console and runs show ip."""
    from validation.checks.vpcs import _drain_until_prompt, _parse_show_ip

    components = await mcp_client.list_components(ctx)
    node = next((c for c in components if c.name == node_name and c.type == "vpcs"), None)
    if node is None:
        return {"error": t("prompt.tool_error.vpcs_not_found", locale, node=node_name)}
    if node.status != "started":
        return {
            "error": t(
                "prompt.tool_error.node_not_started", locale, node=node_name, status=node.status
            ),
            "status": node.status,
        }

    detail = await mcp_client.get_component(ctx, node.id)
    console_port = detail.properties.get("console")
    console_host = detail.properties.get("console_host") or ""

    if not console_port:
        return {"error": t("prompt.tool_error.no_console_port", locale, node=node_name)}

    # GNS3 returns 0.0.0.0 as the listening address, so use the host from the URL instead
    if not console_host or console_host in ("0.0.0.0", "::"):
        derived = urlparse(ctx.environment_url).hostname
        if not derived:
            raise ValueError("environment_url has no host")
        console_host = derived

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(console_host, console_port), timeout=5.0
        )
    except Exception as exc:
        return {"error": t("prompt.tool_error.console_unreachable", locale, error=exc)}

    try:
        writer.write(b"\r\n")
        await writer.drain()
        await asyncio.sleep(0.3)
        await _drain_until_prompt(reader, timeout=0.5)

        writer.write(b"show ip\r\n")
        await writer.drain()

        raw = await _drain_until_prompt(reader, timeout=3.0)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    text = raw.decode("utf-8", errors="replace")
    result = _parse_show_ip(text)
    return {"node": node_name, "ip": result["ip"], "gateway": result["gateway"]}


async def execute_tool(name: str, args: dict, ctx, mcp_client, locale: Locale) -> str:
    """Executes an allowed tool by name and returns the result as a JSON string."""
    if name not in ALLOWED_TOOLS:
        return t("prompt.tool_error.not_allowed", locale, name=name)
    try:
        if name == "list_components":
            data = await mcp_client.list_components(ctx)
        elif name == "get_component":
            data = await mcp_client.get_component(ctx, args["component_id"])
        elif name == "get_vpcs_ip":
            data = await run_vpcs_show_ip(args["node_name"], ctx, mcp_client, locale)
        elif name == "list_errors":
            data = await mcp_client.list_errors(ctx)
        else:
            return t("prompt.tool_error.not_implemented", locale, name=name)
    except Exception as exc:
        return t("prompt.tool_error.failed", locale, name=name, error=exc)

    if isinstance(data, dict):
        return json.dumps(data, ensure_ascii=False, default=str)
    if hasattr(data, "model_dump"):
        return json.dumps(data.model_dump(), ensure_ascii=False, default=str)
    if isinstance(data, list):
        return json.dumps(
            [d.model_dump() if hasattr(d, "model_dump") else d for d in data],
            ensure_ascii=False,
            default=str,
        )
    return json.dumps(data, ensure_ascii=False, default=str)
