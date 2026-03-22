"""Модели HintAgent."""

from pydantic import BaseModel, Field

from learning_analytics.context import AgentContext


class HintInput(BaseModel):
    """Запрос подсказки."""

    session_id: str
    user_id: str
    lab_slug: str
    step_slug: str
    attempts_count: int = Field(default=0, ge=0)
    last_error: str | None = None
    agent_context: AgentContext | None = None


class HintResponse(BaseModel):
    """Подсказка от агента."""

    hint: str
    hint_level: int = Field(ge=1, le=3, description="1=общая, 2=направляющая, 3=конкретная")
    remaining_hints: int = Field(ge=0)
