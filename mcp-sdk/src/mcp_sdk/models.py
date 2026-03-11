"""Стандартные модели данных для MCP-серверов."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class LogLevel(str, Enum):
    """Уровень логирования."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    ALL = "all"


class Component(BaseModel):
    """Универсальное представление элемента системы."""

    id: str
    name: str
    type: str
    status: str
    summary: str


class ComponentDetail(Component):
    """Расширенная информация о компоненте."""

    properties: dict[str, Any]
    configuration: str | None = None
    relationships: list[str]


class SystemOverview(BaseModel):
    """Снимок состояния системы верхнего уровня."""

    system_name: str
    system_version: str | None = None
    component_count: int
    components_by_type: dict[str, int]
    components_by_status: dict[str, int]
    summary: str


class ErrorEntry(BaseModel):
    """Запись об ошибке."""

    timestamp: datetime
    level: LogLevel
    component_id: str | None = None
    message: str
    details: str | None = None


class LogEntry(BaseModel):
    """Запись лога."""

    timestamp: datetime
    level: LogLevel
    source: str
    message: str


class UserAction(BaseModel):
    """Действие пользователя в целевой системе."""

    timestamp: datetime
    component_id: str | None = None
    action: str
    raw_command: str | None = None
    success: bool


class ActionSpec(BaseModel):
    """Спецификация доступного действия."""

    name: str
    description: str
    parameters: dict[str, Any]
    component_types: list[str]


class ActionResult(BaseModel):
    """Результат выполнения действия."""

    success: bool
    message: str
    output: str | None = None
