"""Pydantic schemas for the validation_runs API."""

from datetime import datetime

from pydantic import BaseModel


class ValidationRunListItem(BaseModel):
    """A run list item: status, duration, and checks summary."""

    id: str
    lab_slug: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    passed_checks: int | None
    total_checks: int | None


class ValidationRunDetail(BaseModel):
    """A detailed validation run with the full list of steps."""

    id: str
    lab_slug: str
    status: str
    steps: list
    started_at: datetime
    finished_at: datetime | None
