from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import require_admin, require_internal_caller
from db.session import get_db
from deps import get_locale
from i18n import Locale, LocalizedError
from labs.schemas import (
    LabCreate,
    LabDetailResponse,
    LabResponse,
    LabTemplateResponse,
    SetLabTemplateRequest,
)
from labs.serializers import to_lab_detail_response, to_lab_response
from labs.service import create_lab, delete_lab, get_all_labs, get_lab_by_slug, set_lab_template

router = APIRouter()
internal_router = APIRouter()


@router.get("", response_model=list[LabResponse])
async def list_labs(
    course_slug: str | None = None,
    db: AsyncSession = Depends(get_db),
    locale: Locale = Depends(get_locale),
):
    """Returns the list of enabled labs, optionally filtered by course.

    Disabled labs are hidden: launching one 400s. Admin listings stay unfiltered.
    """
    labs = await get_all_labs(db, course_slug=course_slug, enabled_only=True)
    return [to_lab_response(lab, locale) for lab in labs]


@router.post("", response_model=LabResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_endpoint(
    body: LabCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
    locale: Locale = Depends(get_locale),
):
    """Creates a lab. Returns 409 if the slug is already taken."""
    existing = await get_lab_by_slug(db, body.slug)
    if existing:
        raise LocalizedError("error.lab.already_exists", status_code=status.HTTP_409_CONFLICT)
    lab = await create_lab(
        db,
        slug=body.slug,
        title=body.title,
        description=body.description,
        difficulty=body.difficulty,
        environment_type=body.environment_type,
        gns3_template_project_id=body.gns3_template_project_id,
    )
    return to_lab_response(lab, locale)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lab_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Deletes a lab by slug. Returns 404 if not found."""
    deleted = await delete_lab(db, slug)
    if not deleted:
        raise LocalizedError("error.lab.not_found", status_code=status.HTTP_404_NOT_FOUND)


@router.get("/{slug}", response_model=LabDetailResponse)
async def get_lab(
    slug: str, db: AsyncSession = Depends(get_db), locale: Locale = Depends(get_locale)
):
    """Returns the lab with its steps. Returns 404 if not found."""
    lab = await get_lab_by_slug(db, slug)
    if lab is None:
        raise LocalizedError("error.lab.not_found", status_code=status.HTTP_404_NOT_FOUND)
    return to_lab_detail_response(lab, locale)


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
