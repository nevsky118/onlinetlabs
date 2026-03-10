"""Модели LabAgent."""

from pydantic import BaseModel, Field


class LabQueryInput(BaseModel):
    """Запрос к лаб-среде."""

    session_id: str
    user_id: str
    environment_url: str
    project_id: str
    query: str = Field(description="Что узнать о среде")


class LabActionInput(BaseModel):
    """Команда на выполнение действия в лаб-среде."""

    session_id: str
    user_id: str
    environment_url: str
    project_id: str
    action_name: str
    params: dict = Field(default_factory=dict)


class LabQueryResult(BaseModel):
    """Результат запроса к лаб-среде."""

    success: bool
    summary: str
    components: list[dict] = Field(default_factory=list)
    raw_data: dict | None = None
