"""MCP-тулзы доступные чат-LLM."""

import asyncio
import json
from urllib.parse import urlparse

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_components",
            "description": "Список компонентов (нод и линков) текущей лаб-среды и их статус.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_component",
            "description": "Детальное состояние одного компонента по id.",
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
                "Запустить 'show ip' на VPCS-узле и получить текущий IP-адрес и шлюз. "
                "Используй чтобы проверить что студент настроил правильный IP."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {
                        "type": "string",
                        "description": "Имя узла, например PC1 или PC2",
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
            "description": "Последние ошибки среды.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

ALLOWED_TOOLS = {t["function"]["name"] for t in TOOL_DEFINITIONS}


async def _run_vpcs_show_ip(node_name: str, ctx, mcp_client) -> dict:
    """Подключается telnet к VPCS-консоли и выполняет show ip."""
    from validation.checks.vpcs import _drain_until_prompt, _parse_show_ip

    # Находим ноду по имени
    components = await mcp_client.list_components(ctx)
    node = next(
        (c for c in components if c.name == node_name and c.type == "vpcs"), None
    )
    if node is None:
        return {"error": f"VPCS-узел '{node_name}' не найден"}
    if node.status != "started":
        return {
            "error": f"Узел '{node_name}' не запущен (статус: {node.status})",
            "status": node.status,
        }

    # Получаем консольный порт
    detail = await mcp_client.get_component(ctx, node.id)
    console_port = detail.properties.get("console")
    console_host = detail.properties.get("console_host") or ""

    if not console_port:
        return {"error": f"Нет консольного порта у узла '{node_name}'"}

    # GNS3 отдаёт 0.0.0.0 как listening-адрес — используем хост из URL
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
        return {"error": f"Не удалось подключиться к консоли: {exc}"}

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


async def execute_tool(name: str, args: dict, ctx, mcp_client) -> str:
    """Выполняет разрешённую тулзу по имени и возвращает результат как JSON-строку."""
    if name not in ALLOWED_TOOLS:
        return f"Tool {name} is not allowed."
    try:
        if name == "list_components":
            data = await mcp_client.list_components(ctx)
        elif name == "get_component":
            data = await mcp_client.get_component(ctx, args["component_id"])
        elif name == "get_vpcs_ip":
            data = await _run_vpcs_show_ip(args["node_name"], ctx, mcp_client)
        elif name == "list_errors":
            data = await mcp_client.list_errors(ctx)
        else:
            return f"Tool {name} not implemented."
    except Exception as exc:
        return f"Tool {name} failed: {exc}"

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
