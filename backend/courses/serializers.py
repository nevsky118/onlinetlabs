"""Locale-aware serialization of Course rows into API responses."""

from courses.schemas import CourseDetailResponse, CourseResponse, LabSummary
from i18n import Locale, resolve_localized
from models.course import Course


def to_course_response(course: Course, locale: Locale) -> CourseResponse:
    """Course row to its API shape, with content rendered for the locale."""
    return CourseResponse(
        slug=course.slug,
        title=resolve_localized(course.title_i18n, locale),
        description=resolve_localized(course.description_i18n, locale) or None,
        difficulty=course.difficulty,
        order=course.order,
        meta=course.meta,
    )


def to_course_detail_response(course: Course, locale: Locale) -> CourseDetailResponse:
    """Course row with its labs, content rendered for the locale."""
    base = to_course_response(course, locale)
    return CourseDetailResponse(
        **base.model_dump(),
        labs=[
            LabSummary(
                slug=lab.slug,
                title=resolve_localized(lab.title_i18n, locale),
                difficulty=lab.difficulty,
                environment_type=lab.environment_type,
                order_in_course=lab.order_in_course,
            )
            for lab in course.labs
        ],
    )
