"""Registry of loop tools: default-deny OBSERVE/ACT classification.

The MCP tools' own annotations are considered untrusted -- classification is set here.
An unclassified tool is NOT called (let alone as ACT). allowlist = this registry.
"""

from enum import Enum


class ToolKind(str, Enum):
    OBSERVE = "observe"  # read-only observation (P1)
    ACT = "act"  # intervention on the environment (P2)


# Single default-deny registry (also the allowlist). Only the listed tools can be called.
_REGISTRY: dict[str, ToolKind] = {
    "list_components": ToolKind.OBSERVE,
    "get_component": ToolKind.OBSERVE,
    "list_errors": ToolKind.OBSERVE,
    "get_logs": ToolKind.OBSERVE,
    "list_user_actions": ToolKind.OBSERVE,
    "execute_action": ToolKind.ACT,
}


def classify(tool: str) -> ToolKind | None:
    """The tool's kind, or None if unclassified (forbidden)."""
    return _REGISTRY.get(tool)
