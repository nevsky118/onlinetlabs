# Pydantic schemas для gns3-service API.

from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Запрос на создание лабораторной сессии."""

    user_id: str = Field(
        description="ID пользователя платформы",
        examples=["user-42"],
    )
    lab_template_project_id: str = Field(
        description="UUID шаблонного проекта GNS3, который будет склонирован",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )


class SessionResponse(BaseModel):
    """Данные созданной сессии. Пароль возвращается только один раз."""

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
        description="Пароль (plaintext) — возвращается один раз при создании, в БД хранится хеш",
    )
    gns3_url: str = Field(
        description="URL GNS3-сервера для подключения клиента",
        examples=["http://gns3.example.com:3080"],
    )


class SessionStatus(BaseModel):
    """Текущее состояние сессии."""

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
    """Событие из истории действий в лабораторной сессии."""

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
    """Новые учётные данные после сброса пароля."""

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


class ErrorResponse(BaseModel):
    """Стандартный ответ об ошибке."""

    detail: str = Field(
        description="Описание ошибки",
        examples=["Session not found"],
    )
