"""Admin-роутер: /admin/overview, /admin/identifier-eval, /admin/tk-sensitivity, /admin/users."""
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.data_registry import ADMIN_TABLES, serialize_row
from admin.schemas import (
    AdminDataResponse,
    AdminLab,
    AdminLabUpdate,
    CurvePoint,
    IdentifierEvalResponse,
    OverviewAb,
    OverviewCohort,
    OverviewIdentifier,
    OverviewOps,
    OverviewResponse,
    TkPoint,
    TkSensitivityResponse,
    UserListItem,
    UserListResponse,
    UserUpdate,
)
from auth.dependencies import get_current_user
from config.config_model import LearningAnalyticsConfig
from control.criterion import Costs
from control.derive_thresholds import sensitivity_curve
from db.session import async_session, get_db
from deps import get_gns3_client, get_session_factory
from evaluation.metrics import (
    confusion_matrix,
    first_match_diagnostics,
    j_optimal,
    operating_curve,
)
from evaluation.scenarios import make_normal_scenario, make_struggle_scenario
from labs.service import get_all_labs, get_lab_by_slug, update_lab
from learning_analytics.process_state import ProcessRegime
from models.experiment import ExperimentMetrics
from models.session import LearningSession
from models.user import User, UserRole

router = APIRouter()

# Сетка T_k для operating_curve (сек).
_T_K_GRID = [0.0, 15.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 240.0, 300.0]

# Отношения стоимостей для кривой чувствительности.
_RATIOS = [0.2, 0.5, 1.0, 2.0, 5.0]


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Только администратор (зеркало experiment/router._require_admin)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


def _build_synthetic_scenarios():
    """Синтетические сценарии идентификатора (4 типа × 3 onset + 5 нормальных)."""
    scns = []
    for regime in [
        ProcessRegime.REPEATING_ERRORS,
        ProcessRegime.TRIAL_AND_ERROR,
        ProcessRegime.STUCK_ON_STEP,
        ProcessRegime.IDLE,
    ]:
        for onset in [4, 5, 6]:
            scns.append(make_struggle_scenario(regime, onset_index=onset, n=14, step=15.0))
    for _ in range(5):
        scns.append(make_normal_scenario(n=14, step=15.0))
    return scns


def _build_synthetic_sessions():
    """Синтетические сессии для кривой T_k (зеркало derive_thresholds.__main__)."""
    def _session(spell_len: int, regime: str = "stuck_on_step", t_step: int = 15) -> dict:
        samples, t, dwell = [], 0, 0.0
        while t <= spell_len:
            samples.append({"ts": float(t), "regime": regime, "dwell": dwell})
            t += t_step
            dwell += float(t_step)
        samples.append({"ts": float(t), "regime": "productive", "dwell": 0.0})
        return {"samples": samples}

    return [
        _session(30), _session(30), _session(60),
        _session(120), _session(180), _session(300), _session(600),
    ]


def _default_la_config() -> LearningAnalyticsConfig:
    """Конфиг LA без ENV: дефолтные значения Pydantic."""
    return LearningAnalyticsConfig()


def build_identifier_eval(cfg: LearningAnalyticsConfig | None = None) -> dict:
    """Строит operating-кривую + матрицу + first-match на синтетике. preliminary=True."""
    if cfg is None:
        cfg = _default_la_config()

    scns = _build_synthetic_scenarios()
    costs = Costs(
        c_stuck=cfg.cost_stuck,
        c_intervention=cfg.cost_intervention,
        c_false=cfg.cost_false_intervention,
    )
    curve = operating_curve(scns, _T_K_GRID, cfg, costs)
    opt = j_optimal(curve)

    # confusion_matrix: запускаем harness @ j_optimal_t_k
    from evaluation.harness import run_identifier
    pairs = [(scn, run_identifier(scn, opt.t_k, cfg)) for scn in scns]
    cm_raw = confusion_matrix(pairs)
    # сериализуем ключи в str
    cm_ser = {r.value: {c.value: v for c, v in row.items()} for r, row in cm_raw.items()}

    fm = first_match_diagnostics(scns, cfg)

    return {
        "curve": [
            {
                "t_k": p.t_k,
                "latency_median": p.latency_median,
                "false_per_hour": p.false_per_hour,
                "recall": p.recall,
                "j": p.J,
            }
            for p in curve
        ],
        "j_optimal_t_k": opt.t_k,
        "confusion": cm_ser,
        "first_match": fm,
        "costs": {
            "c_stuck": cfg.cost_stuck,
            "c_intervention": cfg.cost_intervention,
            "c_false": cfg.cost_false_intervention,
        },
        # синтетика → всегда предварительно
        "preliminary": True,
    }


def build_tk_sensitivity(cfg: LearningAnalyticsConfig | None = None) -> dict:
    """Кривая чувствительности T_k по ratios стоимостей на синтетических сессиях."""
    if cfg is None:
        cfg = _default_la_config()

    sessions = _build_synthetic_sessions()
    grid = {"stuck_on_step": _T_K_GRID}

    curve = sensitivity_curve(
        sessions,
        _RATIOS,
        grid,
        base_c_intervention=cfg.cost_intervention,
        c_false=cfg.cost_false_intervention,
        cooldown_seconds=cfg.cooldown_period,
        time_unit_seconds=60.0,
    )

    points = []
    for ratio, tk_dict, j in curve:
        # tk_dict: {regime: float}; берём stuck_on_step как представительный
        t_k_val = tk_dict.get("stuck_on_step", 0.0)
        points.append({"ratio": ratio, "t_k": t_k_val, "J": j})

    return {
        "points": points,
        "costs": {
            "c_stuck": cfg.cost_stuck,
            "c_intervention": cfg.cost_intervention,
        },
    }


async def build_overview(db: AsyncSession) -> dict:
    """KPI-агрегат из БД. Числа — из чистых функций."""
    from cohort.service import compute_cohort_metrics
    from experiment.analysis import compute_arm_analysis

    la_cfg = _default_la_config()

    # A/B
    metrics = (await db.execute(select(ExperimentMetrics))).scalars().all()
    ab = compute_arm_analysis(metrics, mentor_seconds=la_cfg.mentor_handling_seconds)

    # Когорта
    cohort = await compute_cohort_metrics(
        db,
        horizon_seconds=la_cfg.cohort_horizon_days * 86400,
        by_arm=False,
    )
    # pooled: aggregate_cohort отдаёт готовую pooled-ячейку (CohortCell), не dict.
    pooled_cell = cohort.get("pooled")
    pooled_reach = pooled_cell.time_to_competence.reach_rate if pooled_cell else 0.0
    pooled_n = pooled_cell.n if pooled_cell else 0

    # Идентификатор (синтетика)
    eval_data = build_identifier_eval(la_cfg)

    # Ops
    active = (await db.execute(
        select(func.count(LearningSession.id)).where(LearningSession.status == "active")
    )).scalar() or 0
    total_ivs = (await db.execute(
        select(func.coalesce(func.sum(ExperimentMetrics.interventions_received), 0))
    )).scalar() or 0
    labeled_n = len(metrics)  # реальных записей с метриками

    return {
        "ab": {
            "l2_pass_closed": ab.l2_pass_rate_closed,
            "l2_pass_open": ab.l2_pass_rate_open,
            "mentor_hours_saved": ab.mentor_hours_saved,
        },
        "cohort": {
            "pooled_reach_rate": pooled_reach,
            "pooled_n": pooled_n,
        },
        "identifier": {
            "j_optimal_t_k": eval_data["j_optimal_t_k"],
            "recall_at_opt": eval_data["curve"][
                next(
                    i for i, p in enumerate(eval_data["curve"])
                    if p["t_k"] == eval_data["j_optimal_t_k"]
                )
            ]["recall"] if eval_data["curve"] else 0.0,
            "costs": eval_data["costs"],
        },
        "ops": {
            "active_sessions": active,
            "total_interventions": int(total_ivs),
            "labeled_real_n": labeled_n,
        },
    }


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """KPI-агрегат: A/B, когорта, идентификатор, ops."""
    data = await build_overview(db)
    return OverviewResponse(
        ab=OverviewAb(**data["ab"]),
        cohort=OverviewCohort(**data["cohort"]),
        identifier=OverviewIdentifier(**data["identifier"]),
        ops=OverviewOps(**data["ops"]),
    )


@router.get("/identifier-eval", response_model=IdentifierEvalResponse)
def get_identifier_eval(_: dict = Depends(require_admin)):
    """Operating-кривая идентификатора (синтетика, preliminary=True)."""
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
    """Кривая чувствительности T_k по стоимостям (синтетика)."""
    data = build_tk_sensitivity()
    return TkSensitivityResponse(
        points=[TkPoint(**p) for p in data["points"]],
        costs=data["costs"],
    )


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: Literal["name", "email", "role"] = "name",
    order: Literal["asc", "desc"] = "asc",
    search: str | None = None,
    role: UserRole | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
) -> UserListResponse:
    """Список пользователей с пагинацией, сортировкой, поиском и фильтром по роли."""
    col = getattr(User, sort)
    order_col = col.asc() if order == "asc" else col.desc()

    base_q = select(User)
    if search:
        pattern = f"%{search}%"
        base_q = base_q.where(or_(User.name.ilike(pattern), User.email.ilike(pattern)))
    if role is not None:
        base_q = base_q.where(User.role == role.value)

    total = (await db.execute(select(func.count()).select_from(base_q.subquery()))).scalar() or 0

    offset = (page - 1) * page_size
    rows = (
        await db.execute(base_q.order_by(order_col).offset(offset).limit(page_size))
    ).scalars().all()

    return UserListResponse(
        items=[
            UserListItem(
                id=u.id,
                name=u.name,
                email=u.email,
                image=u.image,
                role=u.role,
                can_select_model=u.can_select_model,
                can_view_agent_logs=u.can_view_agent_logs,
                is_active=u.is_active,
            )
            for u in rows
        ],
        total=total,
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
    """Обновить роль/флаги пользователя. Нельзя менять собственную роль."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if body.role is not None and user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя менять собственную роль",
        )

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


def _to_admin_lab(lab) -> AdminLab:
    """Serialize Lab ORM object to AdminLab schema."""
    template_status = (lab.meta or {}).get("template_status", "unknown")
    if lab.environment_type != "gns3":
        template_ready = True
    else:
        template_ready = bool(lab.gns3_template_project_id)
    return AdminLab(
        slug=lab.slug,
        title=lab.title,
        enabled=lab.enabled,
        environment_type=lab.environment_type,
        course_slug=lab.course_slug,
        gns3_template_project_id=lab.gns3_template_project_id,
        gns3_template_project_id_frr=lab.gns3_template_project_id_frr,
        gns3_template_project_id_iosvl2=lab.gns3_template_project_id_iosvl2,
        template_ready=template_ready,
        template_status=template_status,
    )


@router.get("/labs", response_model=list[AdminLab])
async def list_admin_labs(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
) -> list[AdminLab]:
    """Список лаб для администратора."""
    labs = await get_all_labs(db)
    return [_to_admin_lab(lab) for lab in labs]


@router.patch("/labs/{slug}", response_model=AdminLab)
async def patch_admin_lab(
    slug: str,
    body: AdminLabUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
) -> AdminLab:
    """Обновить enabled/gns3_template_project_id* лабы."""
    fields = body.model_dump(exclude_unset=True)
    lab = await update_lab(db, slug, fields)
    if lab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лаба не найдена")
    return _to_admin_lab(lab)


async def _rebuild_worker(slug: str, gns3_client, session_factory=async_session) -> None:
    """Фоновая задача: строит шаблон и обновляет статус лабы в БД."""
    try:
        template_id = await gns3_client.build_template(slug)
        new_status, tid = "ready", template_id
    except Exception:
        new_status, tid = "error", None
    async with session_factory() as session:
        lab = await get_lab_by_slug(session, slug)
        if lab is None:
            return
        if tid:
            lab.gns3_template_project_id = tid
        lab.meta = {**(lab.meta or {}), "template_status": new_status}
        await session.commit()


@router.post("/labs/{slug}/rebuild-template", status_code=202)
async def rebuild_lab_template(
    slug: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
    session_factory=Depends(get_session_factory),
    _: dict = Depends(require_admin),
) -> dict:
    """Запустить пересборку GNS3-шаблона для лабы. Idempotent, возвращает 202."""
    lab = await get_lab_by_slug(db, slug)
    if lab is None:
        raise HTTPException(404, "Лаба не найдена")
    if lab.environment_type != "gns3":
        raise HTTPException(400, "Лаба не использует GNS3")
    if (lab.meta or {}).get("template_status") == "building":
        return {"status": "building"}
    lab.meta = {**(lab.meta or {}), "template_status": "building"}
    await db.commit()
    background_tasks.add_task(_rebuild_worker, slug, gns3_client, session_factory)
    return {"status": "building"}


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
    """Универсальный эндпоинт для чтения whitelisted log-таблиц."""
    spec = ADMIN_TABLES.get(table)
    if spec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown table")

    sort_col = sort if sort in spec.sortable else spec.default_sort
    model = spec.model
    col = getattr(model, sort_col)
    order_col = col.asc() if order == "asc" else col.desc()

    base_q = select(model)
    if search:
        pattern = f"%{search}%"
        base_q = base_q.where(
            or_(*[cast(getattr(model, c), String).ilike(pattern) for c in spec.searchable])
        )

    total = (await db.execute(select(func.count()).select_from(base_q.subquery()))).scalar() or 0

    rows = (
        await db.execute(base_q.order_by(order_col).offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    return AdminDataResponse(
        items=[serialize_row(spec, r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        columns=spec.columns,
        sortable=sorted(spec.sortable),
    )
