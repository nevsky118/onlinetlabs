import logging
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab
from models.session import LearningSession
from sessions.context import build_session_context
from sessions.services.query import get_owned_session

logger = logging.getLogger(__name__)


async def _finalize_experiment_metrics(db: AsyncSession, session: LearningSession) -> None:
    """Computes and saves ExperimentMetrics for the session outcome (best-effort)."""
    from config import settings
    from experiment.assignment import effective_arm, is_l2_session
    from experiment.finalizer import compute_session_metrics
    from models.behavioral_event import BehavioralEvent
    from models.experiment import ExperimentMetrics
    from models.progress import LabProgress
    from models.user import User

    session_id = session.id
    user_id = session.user_id
    lab_slug = session.lab_slug

    # session events
    events_result = await db.execute(
        select(BehavioralEvent).where(BehavioralEvent.session_id == session_id)
    )
    events = events_result.scalars().all()

    arm = await effective_arm(db, user_id, lab_slug)
    l2 = await is_l2_session(db, user_id, lab_slug)

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    experiment_group = (user.experiment_group or "unknown") if user else "unknown"

    # steps from LabProgress
    lp = (await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == user_id,
            LabProgress.lab_slug == lab_slug,
        )
    )).scalar_one_or_none()
    steps_completed = (lp.current_step or 0) if lp else 0

    # total_steps from the YAML spec (authoritative source); fallback → LabStep count or 1
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
        ended_at=session.ended_at or datetime.now(UTC),
        steps_completed=steps_completed,
        total_steps=total_steps,
        experiment_group=experiment_group,
        control_arm=arm.value,
        # base_arm = the user's permanent training arm, not the session's effective arm
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


async def _mark_ended_and_finalize(
    db: AsyncSession, session: LearningSession, status: str
) -> LearningSession:
    """Marks the session ended and captures measurements: ExperimentMetrics + MRT censoring.

    The single finalization point for ALL termination paths (`end_session`, `end_lab`) —
    otherwise the experiment measurement layer (A/B, cohort) stays empty.
    Must be called AFTER stopping the monitor: otherwise late events/interventions
    won't make it into the ExperimentMetrics snapshot.
    """
    session.status = status
    session.ended_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(session)

    # best-effort: finalization error doesn't break session termination
    try:
        await _finalize_experiment_metrics(db, session)
    except Exception:
        logger.exception("Финализация метрик эксперимента упала для сессии %s", session.id)

    # best-effort: MRT points with an unclosed spell are right-censored by session end
    try:
        from learning_analytics.mrt import censor_open_decisions
        await censor_open_decisions(db, session.id)
    except Exception:
        logger.exception("Censoring MRT-точек упал для сессии %s", session.id)

    return session


async def end_session(
    db: AsyncSession, session_id: str, user_id: str, status: str
) -> LearningSession | None:
    """Ends the user's session, setting the status and end time."""
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None
    return await _mark_ended_and_finalize(db, session, status)


async def stop_lab(db, session_id: str, user_id: str, mcp_client) -> bool:
    """Stops all lab nodes via MCP. False if the session isn't owned by the user."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    ctx = build_session_context(session)
    await mcp_client.execute_action(ctx, "stop_all_nodes", {})
    return True


async def restart_lab(db, session_id: str, user_id: str, mcp_client) -> bool:
    """Restarts lab nodes via MCP. False if the session isn't owned by the user."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    ctx = build_session_context(session)
    await mcp_client.execute_action(ctx, "stop_all_nodes", {})
    await mcp_client.execute_action(ctx, "start_all_nodes", {})
    return True


async def reset_lab(db, session_id: str, user_id: str, gns3_client) -> bool:
    """Recreates the GNS3 project from the template and updates the project id in the session."""
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
    """Ends the lab — the path by which the student themself closes the session.

    Step order matters:
    1. Stop the monitor — after this, the stream of behavioral events and
       interventions is closed, so the metrics snapshot will be complete
       (otherwise late interventions are lost).
    2. Finalize measurements (ExperimentMetrics + censoring of open MRT
       points) — BEFORE GNS3 teardown, so an external system failure
       doesn't lose experiment data.
    3. Tear down the gns3-service session (best-effort), release the queue
       and counter.
    """
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    lab_slug = session.lab_slug

    await monitor_registry.stop(session_id)
    await _mark_ended_and_finalize(db, session, status="ended")

    meta = session.meta or {}
    if meta.get("gns3_service_session_id"):
        try:
            await gns3_client.delete_session(meta["gns3_service_session_id"])
        except Exception:
            logger.exception("Teardown gns3-service упал для %s", session_id)
    from sessions.queue import _get_or_create_singleton
    queue = _get_or_create_singleton()
    await queue.release(lab_slug)
    try:
        from observability.metrics import active_sessions_gauge
        active_sessions_gauge.labels(lab_slug=lab_slug).dec()
    except Exception:
        pass  # metrics optional
    return True
