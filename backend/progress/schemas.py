from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CourseProgressResponse(BaseModel):
    """User's progress on a course."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    course_slug: str
    status: str
    score: float | None
    started_at: datetime | None
    completed_at: datetime | None


class LabProgressResponse(BaseModel):
    """User's progress on a lab."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    lab_slug: str
    status: str
    score: float | None
    current_step: int | None
    started_at: datetime | None
    completed_at: datetime | None


class StepAttemptCreate(BaseModel):
    """Data for recording a step attempt."""

    result: str
    score: float | None = None
    error_details: dict | None = None


class StepAttemptResponse(BaseModel):
    """A lab step attempt."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    step_slug: str
    attempt_number: int
    result: str
    score: float | None
    started_at: datetime
    ended_at: datetime | None


class LabProgressDetailResponse(LabProgressResponse):
    """Lab progress together with step attempts."""

    attempts: list[StepAttemptResponse]


class AllProgressResponse(BaseModel):
    """All of the user's progress across courses and labs."""

    courses: list[CourseProgressResponse]
    labs: list[LabProgressResponse]
