"""API endpoints for monitoring and exporting the experiment."""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from experiment.analysis import compute_arm_analysis, compute_experiment_analysis
from experiment.assignment import ExperimentGroup
from experiment.schemas import (
    ArmAnalysisResponse,
    ExperimentStatusResponse,
    GroupUpdateRequest,
    ParticipantResponse,
    TimelineEventResponse,
)
from models.behavioral_event import BehavioralEvent
from models.experiment import ExperimentMetrics
from models.session import LearningSession
from models.user import User

router = APIRouter()


METRICS_EXPORT_FIELDS = [
    "user_id",
    "session_id",
    "experiment_group",
    "agent_backend",
    "total_time_seconds",
    "steps_completed",
    "total_errors",
    "repeated_errors",
    "unique_error_types",
    "interventions_received",
    "interventions_succeeded",
    "interventions_failed",
    "final_score",
    "completed",
]


def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Admin only."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


def _build_status_response(
    counts: dict[str, int], completed: int, in_progress: int
) -> ExperimentStatusResponse:
    """Build status for the final lettered groups of the OpenClaw study."""
    group_a_count = counts.get(ExperimentGroup.GROUP_A.value, 0)
    group_b_count = counts.get(ExperimentGroup.GROUP_B.value, 0)
    return ExperimentStatusResponse(
        total_participants=group_a_count + group_b_count,
        group_a_count=group_a_count,
        group_b_count=group_b_count,
        completed_count=completed,
        in_progress_count=in_progress,
    )


def _metric_to_export_row(metric) -> dict:
    """Convert a metrics object into an export row."""
    return {
        "user_id": metric.user_id,
        "session_id": metric.session_id,
        "experiment_group": metric.experiment_group,
        "agent_backend": getattr(metric, "agent_backend", None),
        "total_time_seconds": metric.total_time_seconds,
        "steps_completed": metric.steps_completed,
        "total_errors": metric.total_errors,
        "repeated_errors": metric.repeated_errors,
        "unique_error_types": metric.unique_error_types,
        "interventions_received": metric.interventions_received,
        "interventions_succeeded": getattr(metric, "interventions_succeeded", 0),
        "interventions_failed": getattr(metric, "interventions_failed", 0),
        "final_score": metric.final_score,
        "completed": metric.completed,
    }


@router.get("/status", response_model=ExperimentStatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Experiment status: participant counts by group."""
    result = await db.execute(
        select(
            User.experiment_group,
            func.count(User.id),
        )
        .where(User.experiment_group.isnot(None))
        .group_by(User.experiment_group)
    )
    counts = {row[0]: row[1] for row in result.all()}

    completed_result = await db.execute(
        select(func.count(ExperimentMetrics.id)).where(ExperimentMetrics.completed.is_(True))
    )
    completed = completed_result.scalar() or 0

    in_progress_result = await db.execute(
        select(func.count(LearningSession.id)).where(LearningSession.status == "active")
    )
    in_progress = in_progress_result.scalar() or 0

    return _build_status_response(counts, completed=completed, in_progress=in_progress)


@router.get("/participants", response_model=list[ParticipantResponse])
async def list_participants(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """List of experiment participants."""
    result = await db.execute(select(User).where(User.experiment_group.isnot(None)))
    users = result.scalars().all()

    participants = []
    for user in users:
        metrics_result = await db.execute(
            select(ExperimentMetrics)
            .where(ExperimentMetrics.user_id == user.id)
            .order_by(ExperimentMetrics.created_at.desc())
            .limit(1)
        )
        latest = metrics_result.scalar_one_or_none()

        sessions_result = await db.execute(
            select(func.count(LearningSession.id)).where(LearningSession.user_id == user.id)
        )
        sessions_count = sessions_result.scalar() or 0

        participants.append(
            ParticipantResponse(
                user_id=user.id,
                email=user.email,
                name=user.name,
                experiment_group=user.experiment_group,
                sessions_count=sessions_count,
                completed=latest.completed if latest else False,
                total_time_seconds=latest.total_time_seconds if latest else None,
            )
        )
    return participants


@router.patch("/participant/{user_id}/group")
async def update_group(
    user_id: str,
    body: GroupUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Reassign a participant's group."""
    if body.group not in (ExperimentGroup.GROUP_A.value, ExperimentGroup.GROUP_B.value):
        raise HTTPException(status_code=400, detail="group must be 'group_a' or 'group_b'")

    await db.execute(update(User).where(User.id == user_id).values(experiment_group=body.group))
    await db.commit()
    return {"ok": True}


@router.get("/session/{session_id}/timeline", response_model=list[TimelineEventResponse])
async def get_session_timeline(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Timeline of session events."""
    result = await db.execute(
        select(BehavioralEvent)
        .where(BehavioralEvent.session_id == session_id)
        .order_by(BehavioralEvent.timestamp)
    )
    events = result.scalars().all()
    return [
        TimelineEventResponse(
            timestamp=e.timestamp,
            event_type=e.event_type,
            action=e.action,
            component_id=e.component_id,
            message=e.message,
            success=e.success,
        )
        for e in events
    ]


@router.get("/metrics")
async def export_metrics(
    format: str = "json",
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Export metrics (json or csv)."""
    result = await db.execute(select(ExperimentMetrics).order_by(ExperimentMetrics.created_at))
    metrics = result.scalars().all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(METRICS_EXPORT_FIELDS)
        for m in metrics:
            row = _metric_to_export_row(m)
            writer.writerow([row[field] for field in METRICS_EXPORT_FIELDS])
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=experiment_metrics.csv"},
        )

    return [_metric_to_export_row(m) for m in metrics]


@router.get("/analysis")
async def get_analysis(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Built-in statistical analysis."""
    result = await db.execute(select(ExperimentMetrics))
    metrics = result.scalars().all()
    return compute_experiment_analysis(metrics)


@router.get("/arm-analysis", response_model=ArmAnalysisResponse)
async def get_arm_analysis(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Comparison of the open vs closed arm on A4-5 metrics."""
    from config import settings

    result = await db.execute(select(ExperimentMetrics))
    metrics = result.scalars().all()
    mentor_seconds = settings.learning_analytics.mentor_handling_seconds
    analysis = compute_arm_analysis(metrics, mentor_seconds=mentor_seconds)
    return ArmAnalysisResponse(
        l2_pass_rate_open=analysis.l2_pass_rate_open,
        l2_pass_rate_closed=analysis.l2_pass_rate_closed,
        escalations_mean_open=analysis.escalations_mean_open,
        escalations_mean_closed=analysis.escalations_mean_closed,
        repeated_errors_comparison=analysis.repeated_errors_comparison,
        mentor_hours_saved=analysis.mentor_hours_saved,
    )
