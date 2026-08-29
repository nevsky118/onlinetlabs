"""Admin console: KPI reports, users, labs and the whitelisted data browser."""

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from admin.data_registry import ADMIN_TABLES
from admin.reports import build_identifier_eval, build_overview, build_tk_sensitivity
from admin.schemas import (
    AdminDataResponse,
    AdminLab,
    AdminLabUpdate,
    AnnotationIrrResponse,
    CurvePoint,
    IdentifierEvalResponse,
    LabProblemOut,
    LabsReadiness,
    OverviewAb,
    OverviewCohort,
    OverviewIdentifier,
    OverviewOps,
    OverviewResponse,
    TemplateBuildStatus,
    TkPoint,
    TkSensitivityResponse,
    UserListItem,
    UserListResponse,
    UserUpdate,
)
from admin.service import browse_table, list_users, rebuild_template, to_admin_lab
from analytics.metrics.annotation import gold_label_count, inter_rater_kappa
from analytics.metrics.reproducibility import build_reproducibility_bundle
from auth.dependencies import require_admin
from i18n import LocalizedError
from kit.db import get_db
from kit.deps import get_gns3_client, get_session_factory
from labs.readiness import audit_labs
from labs.service import get_all_labs, get_lab_by_slug, update_lab
from models.identity import User, UserRole
from validation.runner import spec_slugs

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_user_item(user: User) -> UserListItem:
    """Serializes a user row for the admin console."""
    return UserListItem(
        id=user.id,
        name=user.name,
        email=user.email,
        image=user.image,
        role=user.role,
        can_select_model=user.can_select_model,
        can_view_agent_logs=user.can_view_agent_logs,
        is_active=user.is_active,
    )


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """KPI aggregate: A/B, cohort, identifier, ops."""
    data = await build_overview(db)
    return OverviewResponse(
        ab=OverviewAb(**data["ab"]),
        cohort=OverviewCohort(**data["cohort"]),
        identifier=OverviewIdentifier(**data["identifier"]),
        ops=OverviewOps(**data["ops"]),
    )


@router.get("/identifier-eval", response_model=IdentifierEvalResponse)
def get_identifier_eval(_: dict = Depends(require_admin)):
    """Identifier operating curve (synthetic, preliminary=True)."""
    data = build_identifier_eval()
    return IdentifierEvalResponse(
        curve=[CurvePoint(**p) for p in data["curve"]],
        j_optimal_t_k=data["j_optimal_t_k"],
        confusion=data["confusion"],
        first_match=data["first_match"],
        costs=data["costs"],
        preliminary=data["preliminary"],
    )


@router.get("/tk-sensitivity", response_model=TkSensitivityResponse)
def get_tk_sensitivity(_: dict = Depends(require_admin)):
    """T_k sensitivity curve over costs (synthetic)."""
    data = build_tk_sensitivity()
    return TkSensitivityResponse(
        points=[TkPoint(**p) for p in data["points"]],
        costs=data["costs"],
    )


@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: Literal["name", "email", "role"] = "name",
    order: Literal["asc", "desc"] = "asc",
    search: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
) -> UserListResponse:
    """List of users with pagination, sorting, search, role and activation filter."""
    result = await list_users(
        db,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
        search=search,
        role=role,
        is_active=is_active,
    )
    return UserListResponse(
        items=[_to_user_item(u) for u in result.rows],
        total=result.total,
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{user_id}", response_model=UserListItem)
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserListItem:
    """Update a user's role/flags. Can't change your own role."""
    user = await db.get(User, user_id)
    if user is None:
        raise LocalizedError("error.user.not_found", status_code=404)
    if body.role is not None and user_id == current_user["id"]:
        raise LocalizedError("error.admin.own_role", status_code=400)

    if body.role is not None:
        user.role = body.role.value
    if body.can_select_model is not None:
        user.can_select_model = body.can_select_model
    if body.can_view_agent_logs is not None:
        user.can_view_agent_logs = body.can_view_agent_logs
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return _to_user_item(user)


@router.get("/labs", response_model=list[AdminLab])
async def list_admin_labs(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
) -> list[AdminLab]:
    """List of labs for the administrator."""
    return [to_admin_lab(lab) for lab in await get_all_labs(db)]


@router.get("/labs/readiness", response_model=LabsReadiness)
async def labs_readiness(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
) -> LabsReadiness:
    """Every lab whose declarations do not add up, in one response."""
    problems = audit_labs(await get_all_labs(db), spec_slugs())
    return LabsReadiness(
        ok=not problems,
        problems=[LabProblemOut(slug=p.slug, kind=p.kind, detail=p.detail) for p in problems],
    )


@router.patch("/labs/{slug}", response_model=AdminLab)
async def patch_admin_lab(
    slug: str,
    body: AdminLabUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
) -> AdminLab:
    """Update enabled/gns3_template_project_id* of a lab."""
    lab = await update_lab(db, slug, body.model_dump(exclude_unset=True))
    if lab is None:
        raise LocalizedError("error.lab.not_found", status_code=404)
    return to_admin_lab(lab)


@router.post("/labs/{slug}/rebuild-template", status_code=202, response_model=TemplateBuildStatus)
async def rebuild_lab_template(
    slug: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
    session_factory=Depends(get_session_factory),
    _: dict = Depends(require_admin),
) -> TemplateBuildStatus:
    """Trigger a rebuild of the GNS3 template for a lab. Idempotent, returns 202."""
    lab = await get_lab_by_slug(db, slug)
    if lab is None:
        raise LocalizedError("error.lab.not_found", status_code=404)
    if lab.environment_type != "gns3":
        raise LocalizedError("error.lab.not_gns3", status_code=400)
    if (lab.meta or {}).get("template_status") == "building":
        return TemplateBuildStatus(status="building")
    lab.meta = {**(lab.meta or {}), "template_status": "building"}
    await db.commit()
    background_tasks.add_task(rebuild_template, slug, gns3_client, session_factory)
    return TemplateBuildStatus(status="building")


@router.get("/data/{table}", response_model=AdminDataResponse)
async def get_admin_data(
    table: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    sort: str | None = None,
    order: Literal["asc", "desc"] = "desc",
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
) -> AdminDataResponse:
    """Generic endpoint for reading whitelisted log tables."""
    spec = ADMIN_TABLES.get(table)
    if spec is None:
        raise LocalizedError("error.admin.unknown_table", status_code=status.HTTP_404_NOT_FOUND)

    result = await browse_table(
        db, spec, page=page, page_size=page_size, sort=sort, order=order, search=search
    )
    return AdminDataResponse(
        items=result.rows,
        total=result.total,
        total_is_exact=result.total_is_exact,
        page=page,
        page_size=page_size,
        columns=spec.columns,
        sortable=sorted(spec.sortable),
    )


@router.get("/annotation-irr", response_model=AnnotationIrrResponse)
async def get_annotation_irr(
    session_id: str,
    coder_a: str,
    coder_b: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Cohen's kappa between two annotators, plus the gold-label count.

    Simulated ground truth is excluded by evaluation.annotation, so the count
    reports human labels only.
    """
    return AnnotationIrrResponse(
        gold_label_count=await gold_label_count(db, session_id),
        kappa=await inter_rater_kappa(db, session_id, coder_a, coder_b),
        coder_a=coder_a,
        coder_b=coder_b,
        note="Kappa over windows both coders labelled; sim-truth excluded.",
    )


@router.get("/reproducibility-bundle")
async def get_reproducibility_bundle(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Anonymised MRT bundle for independent re-analysis (simulated users excluded)."""
    return await build_reproducibility_bundle(db)
