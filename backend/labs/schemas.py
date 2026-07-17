from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SetLabTemplateRequest(BaseModel):
    """Request body for binding a GNS3 template_project_id to a lab."""

    template_project_id: str
    variant: Literal["default", "frr", "iosvl2"] = "default"


class LabTemplateResponse(BaseModel):
    """Lab fields related to GNS3 templates."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    gns3_template_project_id: str | None
    gns3_template_project_id_frr: str | None
    gns3_template_project_id_iosvl2: str | None


class LabCreate(BaseModel):
    """Data for creating a lab."""

    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    difficulty: str = "beginner"
    environment_type: str = "none"
    gns3_template_project_id: str | None = None


class LabStepResponse(BaseModel):
    """A lab step."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    step_order: int
    validation_type: str | None


class LabResponse(BaseModel):
    """Lab without nested steps."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    description: str | None
    difficulty: str
    course_slug: str | None
    environment_type: str
    order_in_course: int
    meta: dict | None


class LabDetailResponse(LabResponse):
    """Lab together with its list of steps."""

    steps: list[LabStepResponse]
