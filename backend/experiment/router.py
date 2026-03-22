"""API endpoints для мониторинга и экспорта эксперимента."""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from experiment.analysis import compute_experiment_analysis
from experiment.schemas import (
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


def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Только admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


@router.get("/status", response_model=ExperimentStatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Статус эксперимента: кол-во участников по группам."""
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
        select(func.count(ExperimentMetrics.id))
        .where(ExperimentMetrics.completed.is_(True))
    )
    completed = completed_result.scalar() or 0

    in_progress_result = await db.execute(
        select(func.count(LearningSession.id))
        .where(LearningSession.status == "active")
    )
    in_progress = in_progress_result.scalar() or 0

    total = sum(counts.values())
    return ExperimentStatusResponse(
        total_participants=total,
        control_count=counts.get("control", 0),
        experimental_count=counts.get("experimental", 0),
        completed_count=completed,
        in_progress_count=in_progress,
    )


@router.get("/participants", response_model=list[ParticipantResponse])
async def list_participants(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Список участников эксперимента."""
    result = await db.execute(
        select(User).where(User.experiment_group.isnot(None))
    )
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
            select(func.count(LearningSession.id))
            .where(LearningSession.user_id == user.id)
        )
        sessions_count = sessions_result.scalar() or 0

        participants.append(ParticipantResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            experiment_group=user.experiment_group,
            sessions_count=sessions_count,
            completed=latest.completed if latest else False,
            total_time_seconds=latest.total_time_seconds if latest else None,
        ))
    return participants


@router.patch("/participant/{user_id}/group")
async def update_group(
    user_id: str,
    body: GroupUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Переназначить группу участника."""
    if body.group not in ("control", "experimental"):
        raise HTTPException(status_code=400, detail="group must be 'control' or 'experimental'")

    await db.execute(
        update(User).where(User.id == user_id).values(experiment_group=body.group)
    )
    await db.commit()
    return {"ok": True}


@router.get("/session/{session_id}/timeline", response_model=list[TimelineEventResponse])
async def get_session_timeline(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Хронология событий сессии."""
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
    """Выгрузка метрик (json или csv)."""
    result = await db.execute(
        select(ExperimentMetrics).order_by(ExperimentMetrics.created_at)
    )
    metrics = result.scalars().all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "user_id", "session_id", "experiment_group", "total_time_seconds",
            "steps_completed", "total_errors", "repeated_errors",
            "unique_error_types", "interventions_received", "final_score", "completed",
        ])
        for m in metrics:
            writer.writerow([
                m.user_id, m.session_id, m.experiment_group, m.total_time_seconds,
                m.steps_completed, m.total_errors, m.repeated_errors,
                m.unique_error_types, m.interventions_received, m.final_score, m.completed,
            ])
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=experiment_metrics.csv"},
        )

    return [
        {
            "user_id": m.user_id,
            "session_id": m.session_id,
            "experiment_group": m.experiment_group,
            "total_time_seconds": m.total_time_seconds,
            "steps_completed": m.steps_completed,
            "total_errors": m.total_errors,
            "repeated_errors": m.repeated_errors,
            "unique_error_types": m.unique_error_types,
            "interventions_received": m.interventions_received,
            "final_score": m.final_score,
            "completed": m.completed,
        }
        for m in metrics
    ]


@router.get("/analysis")
async def get_analysis(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """Встроенный статистический анализ."""
    result = await db.execute(select(ExperimentMetrics))
    metrics = result.scalars().all()
    return compute_experiment_analysis(metrics)
