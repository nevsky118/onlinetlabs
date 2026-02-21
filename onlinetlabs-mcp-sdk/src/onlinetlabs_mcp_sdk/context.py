"""Контекст сессии и описание возможностей сервера."""

from typing import Any

from pydantic import BaseModel, Field


class SessionContext(BaseModel):
    """Контекст сессии обучения для маршрутизации к среде студента."""

    user_id: str
    session_id: str
    environment_url: str
    project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ServerCapabilities(BaseModel):
    """Декларация возможностей MCP-сервера."""

    system_name: str
    capabilities: list[str]
    domain_tools: list[str] = Field(default_factory=list)
