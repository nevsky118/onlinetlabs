from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import require_instructor
from db.session import get_db
from instructor.schemas import (
    LabProgressRow,
    SessionSummary,
    StudentDetailResponse,
    StudentOverview,
    StudentsOverviewResponse,
    TimelineItem,
)
from instructor.service import build_session_timeline, get_student_detail, get_students_overview
from models.session import LearningSession

router = APIRouter()


@router.get("/students", response_model=StudentsOverviewResponse)
async def list_students(
    _: dict = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    """Сводная таблица прогресса всех учеников для преподавателя."""
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
    """Детальный прогресс одного ученика с разбивкой по лабам и подсказкам."""
    detail = await get_student_detail(db, user_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    return StudentDetailResponse(
        **{k: v for k, v in detail.items() if k not in ("labs", "sessions")},
        labs=[LabProgressRow(**lab) for lab in detail["labs"]],
        sessions=[SessionSummary(**s) for s in detail["sessions"]],
    )


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
    """Таймлайн диалога студента по сессии (чат + интервенции)."""
    session = (await db.execute(
        select(LearningSession).where(LearningSession.id == session_id)
    )).scalar_one_or_none()
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    items = await build_session_timeline(db, session_id)
    return [TimelineItem(**i) for i in items]
