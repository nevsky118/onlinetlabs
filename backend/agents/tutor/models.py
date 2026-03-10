"""Модели TutorAgent."""

from pydantic import BaseModel, Field


class TutorInput(BaseModel):
    """Вопрос студента к тьютору."""

    session_id: str
    user_id: str
    question: str
    context: str = Field(default="", description="Контекст лабы/курса")
    lab_slug: str | None = None
    step_slug: str | None = None


class TutorResponse(BaseModel):
    """Ответ тьютора."""

    answer: str
    follow_up_questions: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
