from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CourseProgressResponse(BaseModel):
    """Прогресс пользователя по курсу."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    course_slug: str
    status: str
    score: float | None
    started_at: datetime | None
    completed_at: datetime | None


class LabProgressResponse(BaseModel):
    """Прогресс пользователя по лабораторной."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    lab_slug: str
    status: str
    score: float | None
    current_step: int | None
    started_at: datetime | None
    completed_at: datetime | None


class StepAttemptCreate(BaseModel):
    """Данные для записи попытки прохождения шага."""

    result: str
    score: float | None = None
    error_details: dict | None = None


class StepAttemptResponse(BaseModel):
    """Попытка прохождения шага лабораторной."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    step_slug: str
    attempt_number: int
    result: str
    score: float | None
    started_at: datetime
    ended_at: datetime | None


class LabProgressDetailResponse(LabProgressResponse):
    """Прогресс по лабораторной вместе с попытками по шагам."""

    attempts: list[StepAttemptResponse]


class AllProgressResponse(BaseModel):
    """Весь прогресс пользователя по курсам и лабораторным."""

    courses: list[CourseProgressResponse]
    labs: list[LabProgressResponse]
