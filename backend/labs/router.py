from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import require_admin, require_internal_caller
from db.session import get_db
from labs.schemas import (
    LabCreate,
    LabDetailResponse,
    LabResponse,
    LabTemplateResponse,
    SetLabTemplateRequest,
)
from labs.service import create_lab, delete_lab, get_all_labs, get_lab_by_slug, set_lab_template

router = APIRouter()
internal_router = APIRouter()


@router.get("", response_model=list[LabResponse])
async def list_labs(course_slug: str | None = None, db: AsyncSession = Depends(get_db)):
    """Возвращает список лабораторных работ, опционально по курсу."""
    return await get_all_labs(db, course_slug=course_slug)


@router.post("", response_model=LabResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_endpoint(
    body: LabCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Создаёт лабораторную работу. Возвращает 409, если slug уже занят."""
    existing = await get_lab_by_slug(db, body.slug)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lab already exists")
    return await create_lab(
        db,
        slug=body.slug,
        title=body.title,
        description=body.description,
        difficulty=body.difficulty,
        environment_type=body.environment_type,
        gns3_template_project_id=body.gns3_template_project_id,
    )


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lab_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Удаляет лабораторную работу по slug. Возвращает 404, если не найдена."""
    deleted = await delete_lab(db, slug)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")


@router.get("/{slug}", response_model=LabDetailResponse)
async def get_lab(slug: str, db: AsyncSession = Depends(get_db)):
    """Возвращает лабораторную работу с её шагами. Возвращает 404, если не найдена."""
    lab = await get_lab_by_slug(db, slug)
    if lab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")
    return lab


@internal_router.post(
    "/labs/{slug}/gns3-template",
    response_model=LabTemplateResponse,
    tags=["internal"],
)
async def set_gns3_template(
    slug: str,
    body: SetLabTemplateRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_caller),
):
    """Привязывает GNS3 template_project_id к лабе. Только server-to-server."""
    return await set_lab_template(db, slug, body.template_project_id, body.variant)
