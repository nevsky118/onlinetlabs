from pydantic import BaseModel


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
