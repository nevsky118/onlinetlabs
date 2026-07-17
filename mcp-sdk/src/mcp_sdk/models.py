"""Standard data models for MCP servers."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class LogLevel(str, Enum):
    """Log level."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    ALL = "all"


class Component(BaseModel):
    """Generic representation of a system element."""

    id: str
    name: str
    type: str
    status: str
    summary: str


class ComponentDetail(Component):
    """Extended component information."""

    properties: dict[str, Any]
    configuration: str | None = None
    relationships: list[str]


class SystemOverview(BaseModel):
    """Top-level system state snapshot."""

    system_name: str
    system_version: str | None = None
    component_count: int
    components_by_type: dict[str, int]
    components_by_status: dict[str, int]
    summary: str


class ErrorEntry(BaseModel):
    """Error record."""

    timestamp: datetime
    level: LogLevel
    component_id: str | None = None
    message: str
    details: str | None = None


class LogEntry(BaseModel):
    """Log record."""

    timestamp: datetime
    level: LogLevel
    source: str
    message: str


class UserAction(BaseModel):
    """User action in the target system."""

    timestamp: datetime
    component_id: str | None = None
    action: str
    raw_command: str | None = None
    success: bool


class ActionSpec(BaseModel):
    """Specification of an available action."""

    name: str
    description: str
    parameters: dict[str, Any]
    component_types: list[str]


class ActionResult(BaseModel):
    """Result of executing an action."""

    success: bool
    message: str
    output: str | None = None
