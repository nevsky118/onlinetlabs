"""API endpoints for monitoring and exporting the experiment."""

import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.metrics.arm_analysis import compute_arm_analysis
from auth.dependencies import require_admin
from config import settings
from experiment.schemas import (
    ArmAnalysisResponse,
    ParticipantResponse,
    TimelineEventResponse,
)
from experiment.service import (
    METRICS_EXPORT_FIELDS,
    get_all_metrics,
    get_participants,
    get_session_timeline,
    metric_to_export_row,
)
from kit.db import get_db

router = APIRouter(prefix="/experiment", tags=["experiment"])


@router.get("/participants", response_model=list[ParticipantResponse])
async def list_participants(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """List of experiment participants."""
    return [ParticipantResponse(**row) for row in await get_participants(db)]


@router.get("/session/{session_id}/timeline", response_model=list[TimelineEventResponse])
async def session_timeline(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Timeline of session events."""
    return [
        TimelineEventResponse(
            timestamp=event.timestamp,
            event_type=event.event_type,
            action=event.action,
            component_id=event.component_id,
            message=event.message,
            success=event.success,
        )
        for event in await get_session_timeline(db, session_id)
    ]


@router.get("/metrics")
async def export_metrics(
    format: str = "json",
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Export metrics (json or csv)."""
    metrics = await get_all_metrics(db)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(METRICS_EXPORT_FIELDS)
        for metric in metrics:
            row = metric_to_export_row(metric)
            writer.writerow([row[field] for field in METRICS_EXPORT_FIELDS])
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=experiment_metrics.csv"},
        )

    return [metric_to_export_row(metric) for metric in metrics]


@router.get("/arm-analysis", response_model=ArmAnalysisResponse)
async def get_arm_analysis(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Comparison of the open vs closed arm on A4-5 metrics."""
    analysis = compute_arm_analysis(
        await get_all_metrics(db),
        mentor_seconds=settings.learning_analytics.mentor_handling_seconds,
    )
    return ArmAnalysisResponse(
        l2_pass_rate_open=analysis.l2_pass_rate_open,
        l2_pass_rate_closed=analysis.l2_pass_rate_closed,
        escalations_mean_open=analysis.escalations_mean_open,
        escalations_mean_closed=analysis.escalations_mean_closed,
        repeated_errors_comparison=analysis.repeated_errors_comparison,
        mentor_hours_saved=analysis.mentor_hours_saved,
    )
