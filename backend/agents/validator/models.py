"""Модели ValidatorAgent."""

from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    """Результат одной проверки."""

    passed: bool
    check_name: str
    expected: str
    actual: str
    details: str | None = None


class ValidationInput(BaseModel):
    """Вход для валидации шага лабы."""

    session_id: str
    user_id: str
    environment_url: str
    project_id: str
    lab_slug: str
    step_slug: str
    criteria: list[dict] = Field(description="Критерии проверки из LabStep.meta")


class ValidationResult(BaseModel):
    """Результат валидации шага."""

    passed: bool
    score: float = Field(ge=0.0, le=100.0)
    checks: list[CheckResult]
    feedback: str
