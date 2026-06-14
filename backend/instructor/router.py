from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import require_instructor
from db.session import get_db
from instructor.schemas import (
    LabProgressRow,
    StudentDetailResponse,
    StudentOverview,
    StudentsOverviewResponse,
)
from instructor.service import get_student_detail, get_students_overview

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
        **{k: v for k, v in detail.items() if k != "labs"},
        labs=[LabProgressRow(**lab) for lab in detail["labs"]],
    )
