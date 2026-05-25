from pydantic import BaseModel, Field


class LabCreate(BaseModel):
    """Данные для создания лабораторной работы."""

    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    difficulty: str = "beginner"
    environment_type: str = "none"
    gns3_template_project_id: str | None = None


class LabStepResponse(BaseModel):
    """Шаг лабораторной работы."""

    slug: str
    title: str
    step_order: int
    validation_type: str | None


class LabResponse(BaseModel):
    """Лабораторная работа без вложенных шагов."""

    slug: str
    title: str
    description: str | None
    difficulty: str
    course_slug: str | None
    environment_type: str
    order_in_course: int
    meta: dict | None


class LabDetailResponse(LabResponse):
    """Лабораторная работа вместе со списком её шагов."""

    steps: list[LabStepResponse]
