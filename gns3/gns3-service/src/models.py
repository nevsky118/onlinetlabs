# Pydantic schemas for the gns3-service API.

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Request to create a lab session."""

    user_id: str = Field(
        description="ID пользователя платформы",
        examples=["user-42"],
    )
    lab_template_project_id: str = Field(
        description="UUID шаблонного проекта GNS3, который будет склонирован",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )


class SessionResponse(BaseModel):
    """Data of the created session. The password is returned only once."""

    session_id: str = Field(
        description="UUID сессии",
        examples=["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    )
    gns3_jwt: str = Field(
        description="JWT-токен для доступа к GNS3 API от имени пользователя",
    )
    project_id: str = Field(
        description="UUID склонированного проекта в GNS3",
        examples=["b2c3d4e5-f6a7-8901-bcde-f12345678901"],
    )
    gns3_user_id: str = Field(
        description="UUID пользователя в GNS3",
    )
    gns3_username: str = Field(
        description="Имя пользователя в GNS3",
        examples=["student_user42"],
    )
    gns3_password: str = Field(
        description="Пароль в открытом виде, отдаётся один раз. В БД больше не хранится.",
    )
    gns3_url: str = Field(
        description="URL GNS3-сервера для подключения клиента",
        examples=["http://gns3.example.com:3080"],
    )
    gns3_deep_url: str = Field(
        description="Deep-link URL для прямого открытия проекта студента в GNS3 Web UI",
        examples=["http://gns3.example.com:3080/static/web-ui/controller/1/project/<uuid>"],
    )


class SessionStatus(BaseModel):
    """Current state of the session."""

    session_id: str = Field(
        description="UUID сессии",
        examples=["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    )
    status: str = Field(
        description="Статус сессии",
        examples=["active", "closed", "error"],
    )
    project_id: str = Field(
        description="UUID проекта в GNS3",
    )
    gns3_username: str = Field(
        description="Имя пользователя в GNS3",
    )
    created_at: datetime = Field(
        description="Время создания сессии (UTC)",
    )


class HistoryEvent(BaseModel):
    """Event from the action history of a lab session."""

    timestamp: datetime = Field(
        description="Время события (UTC)",
    )
    event_type: str = Field(
        description="Тип события",
        examples=["node.started", "link.created", "node.console"],
    )
    component_id: str | None = Field(
        default=None,
        description="UUID компонента GNS3 (узел, линк и т.д.), если применимо",
    )
    data: dict = Field(
        description="Произвольные данные события",
        examples=[{"node_name": "R1", "status": "started"}],
    )


class PasswordResetResponse(BaseModel):
    """New credentials after password reset."""

    session_id: str = Field(
        description="UUID сессии",
        examples=["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    )
    gns3_jwt: str = Field(
        description="Новый JWT-токен для доступа к GNS3 API",
    )
    gns3_username: str = Field(
        description="Имя пользователя в GNS3 (не меняется)",
        examples=["student_user42"],
    )
    gns3_password: str = Field(
        description="Новый пароль (plaintext) — возвращается один раз",
    )


class ProjectCreate(BaseModel):
    """Request to create a project in GNS3."""

    name: str = Field(description="Имя проекта", examples=["my-lab-template"])


class ProjectResponse(BaseModel):
    """Data of a GNS3 project."""

    project_id: str = Field(description="UUID проекта")
    name: str = Field(description="Имя проекта")


class ProjectResetResponse(BaseModel):
    """Data after resetting the session's project."""

    session_id: str = Field(
        description="UUID сессии",
        examples=["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    )
    project_id: str = Field(
        description="UUID нового склонированного проекта в GNS3",
        examples=["c3d4e5f6-a7b8-9012-cdef-123456789012"],
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(
        description="Описание ошибки",
        examples=["Session not found"],
    )


class NodeState(BaseModel):
    """State of a GNS3 node in the session."""

    id: str = Field(description="UUID узла GNS3")
    name: str = Field(description="Имя узла, видимое студенту")
    node_type: str = Field(
        description="Тип узла GNS3 (dynamips, qemu, ethernet_switch, vpcs и т.д.)"
    )
    status: Literal["started", "stopped", "suspended"] = Field(description="Текущий статус узла")
    console: int | None = Field(description="TCP-порт консоли (telnet/vnc/spice)")
    console_type: str | None = Field(description="Тип консоли: telnet, vnc, spice")
    console_host: str = Field(description="Hostname для подключения к консоли")
    symbol: str = Field(description="Путь к SVG-символу узла внутри GNS3")


class LinkEndpoint(BaseModel):
    """One end of a link between nodes."""

    node_id: str = Field(description="UUID узла на этом конце link'а")
    adapter_number: int = Field(description="Номер сетевого адаптера узла")
    port_number: int = Field(description="Номер порта внутри адаптера")


class LinkState(BaseModel):
    """Link between nodes in the GNS3 topology."""

    id: str = Field(description="UUID линка GNS3")
    nodes: list[LinkEndpoint] = Field(description="Концы link'а (обычно два узла)")


class SessionMetrics(BaseModel):
    """Aggregated session metrics for the UI."""

    nodes_total: int = Field(description="Всего узлов в проекте")
    nodes_started: int = Field(description="Узлов в статусе started")
    links_count: int = Field(description="Количество link'ов")
    uptime_seconds: int = Field(description="Сколько секунд прошло с момента запуска сессии")


class SessionStateResponse(BaseModel):
    """Full session state: nodes, links, metrics."""

    session_id: str = Field(description="UUID сессии")
    project_id: str = Field(description="UUID GNS3-проекта сессии")
    status: Literal["active", "closed"] = Field(description="Статус сессии в gns3-service")
    started_at: datetime = Field(description="Время старта сессии (UTC)")
    nodes: list[NodeState] = Field(description="Список узлов с их статусами")
    links: list[LinkState] = Field(description="Список link'ов")
    metrics: SessionMetrics = Field(description="Агрегированные метрики")
