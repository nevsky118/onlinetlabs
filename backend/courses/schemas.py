from pydantic import BaseModel, ConfigDict


class LabSummary(BaseModel):
    """Brief description of a lab within a course."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    difficulty: str
    environment_type: str
    order_in_course: int


class CourseResponse(BaseModel):
    """Course without nested labs."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    description: str | None
    difficulty: str
    order: int
    meta: dict | None


class CourseDetailResponse(CourseResponse):
    """Course together with its list of labs."""

    labs: list[LabSummary]
