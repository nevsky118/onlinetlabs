from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import require_instructor
from cohort.service import compute_cohort_metrics
from config import settings
from db.session import get_db
from instructor.schemas import (
    CohortMetricsResponse,
    LabProgressRow,
    MCPAuditRow,
    SessionSummary,
    StudentDetailResponse,
    StudentOverview,
    StudentsOverviewResponse,
    TimelineItem,
    cohort_response_from_result,
)
from instructor.service import build_session_timeline, get_student_detail, get_students_overview
from models.mcp_audit import MCPAudit
from models.session import LearningSession

router = APIRouter()


@router.get("/cohort-metrics", response_model=CohortMetricsResponse)
async def cohort_metrics(
    by_arm: bool = False,
    _: dict = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    """Cohort org metrics D3/D4. headline=closed; open+pooled alongside."""
    horizon = settings.learning_analytics.cohort_horizon_days * 86400.0
    out = await compute_cohort_metrics(db, horizon_seconds=horizon, by_arm=by_arm)
    return cohort_response_from_result(out)


@router.get("/students", response_model=StudentsOverviewResponse)
async def list_students(
    _: dict = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    """Summary table of all students' progress for the instructor."""
    result = await get_students_overview(db)
    return StudentsOverviewResponse(
        students=[StudentOverview(**s) for s in result["students"]],
        total_students=result["total_students"],
        total_hints=result["total_hints"],
    )


@router.get("/students/{user_id}", response_model=StudentDetailResponse)
async def student_detail(
    user_id: str,
    _: dict = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    """Detailed progress of one student broken down by lab and hints."""
    detail = await get_student_detail(db, user_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentDetailResponse(
        **{k: v for k, v in detail.items() if k not in ("labs", "sessions")},
        labs=[LabProgressRow(**lab) for lab in detail["labs"]],
        sessions=[SessionSummary(**s) for s in detail["sessions"]],
    )


@router.get("/mcp-audit", response_model=list[MCPAuditRow])
async def list_mcp_audit(
    session_id: str | None = None,
    kind: str | None = None,
    _: dict = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    """Log of MCP calls through the control loop, filterable by session and kind (observe/act)."""
    q = select(MCPAudit).order_by(MCPAudit.ts.desc())
    if session_id is not None:
        q = q.where(MCPAudit.session_id == session_id)
    if kind is not None:
        q = q.where(MCPAudit.kind == kind)
    rows = (await db.execute(q)).scalars().all()
    return [MCPAuditRow.model_validate(r) for r in rows]


@router.get(
    "/students/{user_id}/sessions/{session_id}/timeline",
    response_model=list[TimelineItem],
)
async def student_session_timeline(
    user_id: str,
    session_id: str,
    _: dict = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    """Timeline of a student's session dialogue (chat + interventions)."""
    session = (
        await db.execute(select(LearningSession).where(LearningSession.id == session_id))
    ).scalar_one_or_none()
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    items = await build_session_timeline(db, session_id)
    return [TimelineItem(**i) for i in items]
