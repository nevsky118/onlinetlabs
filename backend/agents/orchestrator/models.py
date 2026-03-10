"""Модели Orchestrator."""

from pydantic import BaseModel, Field


class OrchestratorInput(BaseModel):
    """Входящий запрос в оркестратор."""

    session_id: str
    user_id: str
    intent: str = Field(description="Тип запроса: question | validate | hint | lab | analytics")
    payload: dict = Field(default_factory=dict, description="Данные для целевого агента")


class OrchestratorResponse(BaseModel):
    """Ответ оркестратора."""

    agent_used: str
    success: bool
    data: dict = Field(default_factory=dict)
    error: str | None = None
