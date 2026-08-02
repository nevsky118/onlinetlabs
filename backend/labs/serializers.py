"""Locale-aware serialization of Lab rows into API responses."""

from i18n import Locale, resolve_localized
from labs.schemas import LabDetailResponse, LabResponse, LabStepResponse
from models.lab import Lab


def to_lab_response(lab: Lab, locale: Locale) -> LabResponse:
    """Lab row to its API shape, with content rendered for the locale."""
    return LabResponse(
        slug=lab.slug,
        title=resolve_localized(lab.title_i18n, locale),
        description=resolve_localized(lab.description_i18n, locale) or None,
        difficulty=lab.difficulty,
        course_slug=lab.course_slug,
        environment_type=lab.environment_type,
        order_in_course=lab.order_in_course,
        meta=lab.meta,
    )


def to_lab_detail_response(lab: Lab, locale: Locale) -> LabDetailResponse:
    """Lab row with its steps, content rendered for the locale."""
    base = to_lab_response(lab, locale)
    return LabDetailResponse(
        **base.model_dump(),
        steps=[LabStepResponse.model_validate(step) for step in lab.steps],
    )
