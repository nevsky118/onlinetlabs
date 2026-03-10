from pydantic import BaseModel, Field


class LabCreate(BaseModel):
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    difficulty: str = "beginner"
    environment_type: str = "none"


class LabStepResponse(BaseModel):
    slug: str
    title: str
    step_order: int
    validation_type: str | None


class LabResponse(BaseModel):
    slug: str
    title: str
    description: str | None
    difficulty: str
    course_slug: str | None
    environment_type: str
    order_in_course: int
    meta: dict | None


class LabDetailResponse(LabResponse):
    steps: list[LabStepResponse]
