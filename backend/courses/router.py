from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from courses.schemas import CourseDetailResponse, CourseResponse
from courses.service import get_all_courses, get_course_by_slug
from db.session import get_db

router = APIRouter()


@router.get("", response_model=list[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db)):
    """Returns the list of all courses."""
    return await get_all_courses(db)


@router.get("/{slug}", response_model=CourseDetailResponse)
async def get_course(slug: str, db: AsyncSession = Depends(get_db)):
    """Returns the course with its list of labs. Returns 404 if not found."""
    course = await get_course_by_slug(db, slug)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course
