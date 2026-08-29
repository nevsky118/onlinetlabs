"""Queries and export shaping for the experiment API."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.identity import User
from models.learning import LearningSession
from models.research import BehavioralEvent, ExperimentMetrics

# Column order of the CSV export.
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

_ENROLLED = User.control_arm.isnot(None)


def metric_to_export_row(metric) -> dict:
    """Flattens a metrics row into the export column order."""
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


async def get_participants(db: AsyncSession) -> list[dict]:
    """Every enrolled user with their session count and latest metrics row.

    Three grouped queries rather than two per participant, so the roster stays
    flat as the study grows.
    """
    users = (await db.execute(select(User).where(_ENROLLED))).scalars().all()
    if not users:
        return []

    counts = dict(
        (
            await db.execute(
                select(LearningSession.user_id, func.count(LearningSession.id))
                .join(User, User.id == LearningSession.user_id)
                .where(_ENROLLED)
                .group_by(LearningSession.user_id)
            )
        ).all()
    )

    # Ascending order, so the last row written per user is the newest.
    latest: dict[str, ExperimentMetrics] = {}
    rows = (
        await db.execute(
            select(ExperimentMetrics)
            .join(User, User.id == ExperimentMetrics.user_id)
            .where(_ENROLLED)
            .order_by(ExperimentMetrics.user_id, ExperimentMetrics.created_at)
        )
    ).scalars()
    for row in rows:
        latest[row.user_id] = row

    return [
        {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "control_arm": user.control_arm,
            "sessions_count": counts.get(user.id, 0),
            "completed": latest[user.id].completed if user.id in latest else False,
            "total_time_seconds": latest[user.id].total_time_seconds if user.id in latest else None,
        }
        for user in users
    ]


async def get_session_timeline(db: AsyncSession, session_id: str) -> list[BehavioralEvent]:
    """Behavioural events of one session, oldest first."""
    result = await db.execute(
        select(BehavioralEvent)
        .where(BehavioralEvent.session_id == session_id)
        .order_by(BehavioralEvent.timestamp)
    )
    return list(result.scalars().all())


async def get_all_metrics(db: AsyncSession) -> list[ExperimentMetrics]:
    """Every metrics row, oldest first."""
    result = await db.execute(select(ExperimentMetrics).order_by(ExperimentMetrics.created_at))
    return list(result.scalars().all())
