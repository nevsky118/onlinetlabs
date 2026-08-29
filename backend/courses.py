"""Course catalogue: read-only listing and detail."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from i18n import Locale, LocalizedError, resolve_localized
from kit.db import get_db
from kit.deps import get_locale
from models.catalog import Course


class LabSummary(BaseModel):
    """Brief description of a lab within a course."""

    slug: str
    title: str
    difficulty: str
    environment_type: str
    order_in_course: int


class CourseResponse(BaseModel):
    """Course without nested labs."""

    slug: str
    title: str
    description: str | None
    difficulty: str
    order: int
    meta: dict | None


class CourseDetailResponse(CourseResponse):
    """Course together with its list of labs."""

    labs: list[LabSummary]


async def get_all_courses(db: AsyncSession) -> list[Course]:
    """Selects all courses from the DB, ordered by sort order."""
    result = await db.execute(select(Course).order_by(Course.order))
    return list(result.scalars().all())


async def get_course_by_slug(db: AsyncSession, slug: str) -> Course | None:
    """Returns the course by slug with its labs, or None."""
    result = await db.execute(
        select(Course).options(selectinload(Course.labs)).where(Course.slug == slug)
    )
    return result.scalar_one_or_none()


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


router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db), locale: Locale = Depends(get_locale)):
    """Returns the list of all courses."""
    courses = await get_all_courses(db)
    return [to_course_response(course, locale) for course in courses]


@router.get("/{slug}", response_model=CourseDetailResponse)
async def get_course(
    slug: str, db: AsyncSession = Depends(get_db), locale: Locale = Depends(get_locale)
):
    """Returns the course with its list of labs. Returns 404 if not found."""
    course = await get_course_by_slug(db, slug)
    if course is None:
        raise LocalizedError("error.course.not_found", status_code=status.HTTP_404_NOT_FOUND)
    return to_course_detail_response(course, locale)
