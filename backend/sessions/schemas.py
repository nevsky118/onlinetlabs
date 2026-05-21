from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LearningSessionCreate(BaseModel):
    """Данные для создания учебной сессии по slug лабораторной."""

    lab_slug: str


class LearningSessionUpdate(BaseModel):
    """Изменение статуса учебной сессии."""

    status: str


class SessionMeta(BaseModel):
    """Метаданные сессии GNS3 с зашифрованными паролем и JWT."""

    gns3_service_session_id: str
    gns3_user_id: str
    gns3_username: str
    gns3_project_id: str
    enc_password: str
    enc_jwt: str


class LearningSessionResponse(BaseModel):
    """Учебная сессия в ответе API."""

    id: str
    lab_slug: str
    lab_title: str | None = None
    status: str
    started_at: datetime
    ended_at: datetime | None
    meta: dict | None


class LaunchResponse(BaseModel):
    """Ответ на запуск сессии с доступами и ссылками на GNS3."""

    session_id: str
    status: str
    gns3_username: str
    gns3_password: str
    gns3_url: str
    gns3_deep_url: str


class CredentialsResponse(BaseModel):
    """Доступы и ссылки на GNS3 для активной сессии."""

    gns3_username: str
    gns3_password: str
    gns3_url: str
    gns3_deep_url: str


class NodeStateSchema(BaseModel):
    """Состояние узла топологии GNS3."""

    id: str
    name: str
    node_type: str = Field(alias="nodeType")
    status: Literal["started", "stopped", "suspended"]
    console: int | None
    console_type: str | None = Field(alias="consoleType")
    console_host: str = Field(alias="consoleHost")
    symbol: str

    model_config = {"populate_by_name": True}


class LinkEndpointSchema(BaseModel):
    """Конец связи с указанием узла, адаптера и порта."""

    node_id: str = Field(alias="nodeId")
    adapter_number: int = Field(alias="adapterNumber")
    port_number: int = Field(alias="portNumber")

    model_config = {"populate_by_name": True}


class LinkStateSchema(BaseModel):
    """Связь между двумя концами узлов топологии."""

    id: str
    nodes: list[LinkEndpointSchema]


class SessionMetricsSchema(BaseModel):
    """Сводные метрики топологии сессии."""

    nodes_total: int = Field(alias="nodesTotal")
    nodes_started: int = Field(alias="nodesStarted")
    links_count: int = Field(alias="linksCount")
    uptime_seconds: int = Field(alias="uptimeSeconds")

    model_config = {"populate_by_name": True}


class LabRef(BaseModel):
    """Краткая ссылка на лабораторную по slug и заголовку."""

    slug: str
    title: str | None = None


class FullSessionStateResponse(BaseModel):
    """Полное состояние сессии с узлами, связями и метриками."""

    session_id: str = Field(alias="sessionId")
    status: Literal["provisioning", "active", "ended", "error"]
    started_at: datetime = Field(alias="startedAt")
    lab: LabRef
    nodes: list[NodeStateSchema]
    links: list[LinkStateSchema]
    metrics: SessionMetricsSchema

    model_config = {"populate_by_name": True}


class ActivityEventSchema(BaseModel):
    """Событие активности в рамках сессии."""

    timestamp: datetime
    event_type: str = Field(alias="eventType")
    component_id: str | None = Field(alias="componentId")
    data: dict

    model_config = {"populate_by_name": True}


class ActivityResponseSchema(BaseModel):
    """Лента событий активности с курсором для подгрузки."""

    events: list[ActivityEventSchema]
    next_cursor: str | None = Field(alias="nextCursor")

    model_config = {"populate_by_name": True}


class ChatMessageResponse(BaseModel):
    """Сообщение чата сессии в ответе API."""

    id: str
    role: str
    parts: list
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
