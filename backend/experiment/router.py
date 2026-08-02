"""API endpoints for monitoring and exporting the experiment."""

import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import require_admin
from db.session import get_db
from evaluation.arm_analysis import compute_arm_analysis
from experiment.schemas import (
    ArmAnalysisResponse,
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


@router.get("/participants", response_model=list[ParticipantResponse])
async def list_participants(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """List of experiment participants."""
    result = await db.execute(select(User).where(User.control_arm.isnot(None)))
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
                control_arm=user.control_arm,
                sessions_count=sessions_count,
                completed=latest.completed if latest else False,
                total_time_seconds=latest.total_time_seconds if latest else None,
            )
        )
    return participants


@router.get("/session/{session_id}/timeline", response_model=list[TimelineEventResponse])
async def get_session_timeline(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
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
    _: dict = Depends(require_admin),
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


@router.get("/arm-analysis", response_model=ArmAnalysisResponse)
async def get_arm_analysis(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
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
