from datetime import datetime

from pydantic import BaseModel


class StudentOverview(BaseModel):
    """Сводка по одному ученику для общей таблицы кабинета преподавателя."""

    user_id: str
    name: str | None
    email: str | None
    labs_total: int
    labs_completed: int
    labs_in_progress: int
    avg_score: float | None
    total_hints: int
    total_sessions: int
    last_active_at: datetime | None


class StudentsOverviewResponse(BaseModel):
    """Список учеников со сводной статистикой и агрегатами по группе."""

    students: list[StudentOverview]
    total_students: int
    total_hints: int


class LabProgressRow(BaseModel):
    """Прогресс ученика по одной лабе с числом подсказок и попыток."""

    lab_slug: str
    lab_title: str
    status: str
    score: float | None
    current_step: int | None
    hints: int
    sessions: int
    attempts: int
    started_at: datetime | None
    completed_at: datetime | None
    last_active_at: datetime | None


class StudentDetailResponse(BaseModel):
    """Детальная карточка ученика: профиль и прогресс по всем лабам."""

    user_id: str
    name: str | None
    email: str | None
    role: str
    labs_completed: int
    labs_in_progress: int
    avg_score: float | None
    total_hints: int
    total_sessions: int
    labs: list[LabProgressRow]
