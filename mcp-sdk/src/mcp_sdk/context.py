"""Session context and server capability description."""

from typing import Any

from pydantic import BaseModel, Field


class SessionContext(BaseModel):
    """Learning session context for routing to the student's environment."""

    user_id: str
    session_id: str
    environment_url: str
    project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ServerCapabilities(BaseModel):
    """Declaration of MCP server capabilities."""

    system_name: str
    capabilities: list[str]
    domain_tools: list[str] = Field(default_factory=list)
