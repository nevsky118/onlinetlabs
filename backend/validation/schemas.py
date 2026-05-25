"""Pydantic-схемы для validation_runs API."""

from datetime import datetime

from pydantic import BaseModel


class ValidationRunListItem(BaseModel):
    """Элемент списка прогонов: статус, длительность и сводка по проверкам."""

    id: str
    lab_slug: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    passed_checks: int | None
    total_checks: int | None


class ValidationRunDetail(BaseModel):
    """Детальный прогон валидации с полным списком шагов."""

    id: str
    lab_slug: str
    status: str
    steps: list
    started_at: datetime
    finished_at: datetime | None
