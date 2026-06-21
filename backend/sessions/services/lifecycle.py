import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab
from models.session import LearningSession
from sessions.context import build_session_context
from sessions.services.query import get_owned_session

logger = logging.getLogger(__name__)


async def _finalize_experiment_metrics(db: AsyncSession, session: LearningSession) -> None:
    """Вычисляет и сохраняет ExperimentMetrics по итогам сессии (best-effort)."""
    from config import settings
    from experiment.arm_resolver import effective_arm, is_l2_session
    from experiment.finalizer import compute_session_metrics
    from models.behavioral_event import BehavioralEvent
    from models.experiment import ExperimentMetrics
    from models.progress import LabProgress
    from models.user import User

    session_id = session.id
    user_id = session.user_id
    lab_slug = session.lab_slug

    # события сессии
    events_result = await db.execute(
        select(BehavioralEvent).where(BehavioralEvent.session_id == session_id)
    )
    events = events_result.scalars().all()

    arm = await effective_arm(db, user_id, lab_slug)
    l2 = await is_l2_session(db, user_id, lab_slug)

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    experiment_group = (user.experiment_group or "unknown") if user else "unknown"

    # шаги из LabProgress
    lp = (await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == user_id,
            LabProgress.lab_slug == lab_slug,
        )
    )).scalar_one_or_none()
    steps_completed = (lp.current_step or 0) if lp else 0

    # total_steps из YAML-спеки (авторитетный источник); fallback → LabStep count или 1
    from validation.runner import load_lab_spec
    spec = load_lab_spec(lab_slug)
    total_steps = len(spec.get("steps", [])) if spec else 0
    if total_steps == 0:
        from models.lab import LabStep
        total_steps_result = await db.execute(
            select(LabStep).where(LabStep.lab_slug == lab_slug)
        )
        total_steps = len(total_steps_result.scalars().all()) or 1

    la_cfg = settings.learning_analytics
    metrics_dict = compute_session_metrics(
        events=events,
        started_at=session.started_at,
        ended_at=session.ended_at or datetime.now(timezone.utc),
        steps_completed=steps_completed,
        total_steps=total_steps,
        experiment_group=experiment_group,
        control_arm=arm.value,
        # base_arm = постоянный training-arm пользователя, не effective arm сессии
        base_arm=user.control_arm if user else None,
        l2_intervention_cap=la_cfg.l2_intervention_cap,
        is_l2=l2,
    )

    db.add(ExperimentMetrics(
        id=str(uuid4()),
        session_id=session_id,
        user_id=user_id,
        lab_slug=lab_slug,
        **metrics_dict,
    ))
    await db.commit()


async def end_session(
    db: AsyncSession, session_id: str, user_id: str, status: str
) -> LearningSession | None:
    """Завершает сессию пользователя, проставляя статус и время окончания."""
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None
    session.status = status
    session.ended_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)

    # best-effort: ошибка финализации не ломает завершение сессии
    try:
        await _finalize_experiment_metrics(db, session)
    except Exception:
        logger.exception("Финализация метрик эксперимента упала для сессии %s", session_id)

    return session


async def stop_lab(db, session_id: str, user_id: str, mcp_client) -> bool:
    """Останавливает все узлы лабораторной через MCP. False если сессия чужая."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    ctx = build_session_context(session)
    await mcp_client.execute_action(ctx, "stop_all_nodes", {})
    return True


async def restart_lab(db, session_id: str, user_id: str, mcp_client) -> bool:
    """Перезапускает узлы лабораторной через MCP. False если сессия чужая."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    ctx = build_session_context(session)
    await mcp_client.execute_action(ctx, "stop_all_nodes", {})
    await mcp_client.execute_action(ctx, "start_all_nodes", {})
    return True


async def reset_lab(db, session_id: str, user_id: str, gns3_client) -> bool:
    """Пересоздаёт проект GNS3 из шаблона и обновляет id проекта в сессии."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    lab = await db.get(Lab, session.lab_slug)
    if session.lab_slug.endswith("-ccna"):
        template_pid = lab.gns3_template_project_id_iosvl2
    else:
        template_pid = lab.gns3_template_project_id
    meta = dict(session.meta or {})
    result = await gns3_client.reset_project(meta["gns3_service_session_id"], template_pid)
    meta["gns3_project_id"] = result["project_id"]
    session.meta = meta  # reassign so SQLAlchemy detects JSON change
    await db.commit()
    return True


async def end_lab(db, session_id: str, user_id: str, gns3_client, monitor_registry) -> bool:
    """Завершает лабораторную.

    Удаляет сессию gns3-service, останавливает монитор, помечает сессию ended,
    освобождает место в очереди и уменьшает счётчик активных сессий.
    """
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    meta = session.meta or {}
    if meta.get("gns3_service_session_id"):
        try:
            await gns3_client.delete_session(meta["gns3_service_session_id"])
        except Exception:
            logger.exception("Teardown gns3-service упал для %s", session_id)
    await monitor_registry.stop(session_id)
    lab_slug = session.lab_slug
    session.status = "ended"
    session.ended_at = datetime.now(timezone.utc)
    await db.commit()
    from sessions.queue import _get_or_create_singleton
    queue = _get_or_create_singleton()
    await queue.release(lab_slug)
    try:
        from observability.metrics import active_sessions_gauge
        active_sessions_gauge.labels(lab_slug=lab_slug).dec()
    except Exception:
        pass  # metrics optional
    return True
