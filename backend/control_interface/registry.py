"""Реестр инструментов контура: default-deny классификация OBSERVE/ACT.

Аннотации самих MCP-инструментов считаются недоверенными — классификация задаётся здесь.
Неклассифицированный инструмент НЕ вызывается (тем более как ACT). allowlist = этот реестр.
"""
from enum import Enum


class ToolKind(str, Enum):
    OBSERVE = "observe"  # read-only наблюдение (П1)
    ACT = "act"          # воздействие на среду (П2)


# Единый default-deny реестр (он же allowlist). Только перечисленные инструменты вызываемы.
_REGISTRY: dict[str, ToolKind] = {
    "list_components": ToolKind.OBSERVE,
    "get_component": ToolKind.OBSERVE,
    "list_errors": ToolKind.OBSERVE,
    "get_logs": ToolKind.OBSERVE,
    "list_user_actions": ToolKind.OBSERVE,
    "execute_action": ToolKind.ACT,
}


def classify(tool: str) -> ToolKind | None:
    """Вид инструмента или None, если не классифицирован (запрещён)."""
    return _REGISTRY.get(tool)
