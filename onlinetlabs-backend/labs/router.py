from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from labs.schemas import LabDetailResponse, LabResponse, LabStepResponse
from labs.service import get_all_labs, get_lab_by_slug

router = APIRouter()


@router.get("", response_model=list[LabResponse])
async def list_labs(course_slug: str | None = None, db: AsyncSession = Depends(get_db)):
    labs = await get_all_labs(db, course_slug=course_slug)
    return [
        LabResponse(
            slug=lab.slug,
            title=lab.title,
            description=lab.description,
            difficulty=lab.difficulty,
            course_slug=lab.course_slug,
            environment_type=lab.environment_type,
            order_in_course=lab.order_in_course,
            meta=lab.meta,
        )
        for lab in labs
    ]


@router.get("/{slug}", response_model=LabDetailResponse)
async def get_lab(slug: str, db: AsyncSession = Depends(get_db)):
    lab = await get_lab_by_slug(db, slug)
    if lab is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found"
        )
    return LabDetailResponse(
        slug=lab.slug,
        title=lab.title,
        description=lab.description,
        difficulty=lab.difficulty,
        course_slug=lab.course_slug,
        environment_type=lab.environment_type,
        order_in_course=lab.order_in_course,
        meta=lab.meta,
        steps=[
            LabStepResponse(
                slug=s.slug,
                title=s.title,
                step_order=s.step_order,
                validation_type=s.validation_type,
            )
            for s in lab.steps
        ],
    )
