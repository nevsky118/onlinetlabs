from datetime import datetime

from pydantic import BaseModel


class CourseProgressResponse(BaseModel):
    id: str
    course_slug: str
    status: str
    score: float | None
    started_at: datetime | None
    completed_at: datetime | None


class LabProgressResponse(BaseModel):
    id: str
    lab_slug: str
    status: str
    score: float | None
    current_step: int | None
    started_at: datetime | None
    completed_at: datetime | None


class StepAttemptCreate(BaseModel):
    result: str
    score: float | None = None
    error_details: dict | None = None


class StepAttemptResponse(BaseModel):
    id: str
    step_slug: str
    attempt_number: int
    result: str
    score: float | None
    started_at: datetime
    ended_at: datetime | None


class LabProgressDetailResponse(LabProgressResponse):
    attempts: list[StepAttemptResponse]


class AllProgressResponse(BaseModel):
    courses: list[CourseProgressResponse]
    labs: list[LabProgressResponse]
