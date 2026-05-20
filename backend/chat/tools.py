"""Read-only MCP-тулзы, доступные чат-LLM. Деструктив исключён намеренно."""

import json

TOOL_DEFINITIONS = [
    {"type": "function", "function": {"name": "list_components", "description": "Список компонентов (нод) текущей лаб-среды и их статус.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_component", "description": "Детальное состояние одного компонента по id.", "parameters": {"type": "object", "properties": {"component_id": {"type": "string"}}, "required": ["component_id"]}}},
    {"type": "function", "function": {"name": "get_logs", "description": "Последние логи среды.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "list_errors", "description": "Последние ошибки среды.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

ALLOWED_TOOLS = {t["function"]["name"] for t in TOOL_DEFINITIONS}


async def execute_tool(name: str, args: dict, ctx, mcp_client) -> str:
    """Выполняет разрешённую MCP-тулзу по имени и возвращает результат как JSON-строку."""
    if name not in ALLOWED_TOOLS:
        return f"Tool {name} is not allowed."
    try:
        if name == "list_components":
            data = await mcp_client.list_components(ctx)
        elif name == "get_component":
            data = await mcp_client.get_component(ctx, args["component_id"])
        elif name == "get_logs":
            data = await mcp_client.get_logs(ctx)
        elif name == "list_errors":
            data = await mcp_client.list_errors(ctx)
        else:
            return f"Tool {name} not implemented."
    except Exception as exc:
        return f"Tool {name} failed: {exc}"
    if hasattr(data, "model_dump"):
        return json.dumps(data.model_dump(), ensure_ascii=False, default=str)
    if isinstance(data, list):
        return json.dumps([d.model_dump() if hasattr(d, "model_dump") else d for d in data], ensure_ascii=False, default=str)
    return json.dumps(data, ensure_ascii=False, default=str)
