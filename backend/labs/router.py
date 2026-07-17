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
    """Returns the list of labs, optionally filtered by course."""
    return await get_all_labs(db, course_slug=course_slug)


@router.post("", response_model=LabResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_endpoint(
    body: LabCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Creates a lab. Returns 409 if the slug is already taken."""
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
    """Deletes a lab by slug. Returns 404 if not found."""
    deleted = await delete_lab(db, slug)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")


@router.get("/{slug}", response_model=LabDetailResponse)
async def get_lab(slug: str, db: AsyncSession = Depends(get_db)):
    """Returns the lab with its steps. Returns 404 if not found."""
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
    """Binds a GNS3 template_project_id to the lab. Server-to-server only."""
    return await set_lab_template(db, slug, body.template_project_id, body.variant)
