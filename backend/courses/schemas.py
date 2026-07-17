from pydantic import BaseModel, ConfigDict


class LabSummary(BaseModel):
    """Краткое описание лабораторной работы в составе курса."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    difficulty: str
    environment_type: str
    order_in_course: int


class CourseResponse(BaseModel):
    """Курс без вложенных лабораторных работ."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    description: str | None
    difficulty: str
    order: int
    meta: dict | None


class CourseDetailResponse(CourseResponse):
    """Курс вместе со списком его лабораторных работ."""

    labs: list[LabSummary]
