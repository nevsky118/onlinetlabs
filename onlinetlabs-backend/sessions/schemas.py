from datetime import datetime

from pydantic import BaseModel


class LearningSessionCreate(BaseModel):
    lab_slug: str


class LearningSessionUpdate(BaseModel):
    status: str


class LearningSessionResponse(BaseModel):
    id: str
    lab_slug: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    meta: dict | None
