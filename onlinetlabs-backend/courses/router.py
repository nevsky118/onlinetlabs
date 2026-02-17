from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from courses.schemas import CourseDetailResponse, CourseResponse, LabSummary
from courses.service import get_all_courses, get_course_by_slug
from db.session import get_db

router = APIRouter()


@router.get("", response_model=list[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db)):
    courses = await get_all_courses(db)
    return [
        CourseResponse(
            slug=c.slug,
            title=c.title,
            description=c.description,
            difficulty=c.difficulty,
            order=c.order,
            meta=c.meta,
        )
        for c in courses
    ]


@router.get("/{slug}", response_model=CourseDetailResponse)
async def get_course(slug: str, db: AsyncSession = Depends(get_db)):
    course = await get_course_by_slug(db, slug)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    return CourseDetailResponse(
        slug=course.slug,
        title=course.title,
        description=course.description,
        difficulty=course.difficulty,
        order=course.order,
        meta=course.meta,
        labs=[
            LabSummary(
                slug=lab.slug,
                title=lab.title,
                difficulty=lab.difficulty,
                environment_type=lab.environment_type,
                order_in_course=lab.order_in_course,
            )
            for lab in course.labs
        ],
    )
