from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from courses.schemas import CourseDetailResponse, CourseResponse
from courses.serializers import to_course_detail_response, to_course_response
from courses.service import get_all_courses, get_course_by_slug
from db.session import get_db
from deps import get_locale
from i18n import Locale, LocalizedError

router = APIRouter()


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
