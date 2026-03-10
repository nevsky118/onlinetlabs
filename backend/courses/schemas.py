from pydantic import BaseModel


class LabSummary(BaseModel):
    slug: str
    title: str
    difficulty: str
    environment_type: str
    order_in_course: int


class CourseResponse(BaseModel):
    slug: str
    title: str
    description: str | None
    difficulty: str
    order: int
    meta: dict | None


class CourseDetailResponse(CourseResponse):
    labs: list[LabSummary]
