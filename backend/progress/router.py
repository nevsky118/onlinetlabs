from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from progress.schemas import (
    AllProgressResponse,
    CourseProgressResponse,
    LabProgressDetailResponse,
    LabProgressResponse,
    StepAttemptCreate,
    StepAttemptResponse,
)
from progress.service import (
    get_all_progress,
    get_lab_progress_detail,
    record_step_attempt,
    start_lab,
)

router = APIRouter()


@router.get("", response_model=AllProgressResponse)
async def get_progress(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_all_progress(db, current_user["id"])
    return AllProgressResponse(
        courses=[
            CourseProgressResponse(
                id=cp.id,
                course_slug=cp.course_slug,
                status=cp.status,
                score=cp.score,
                started_at=cp.started_at,
                completed_at=cp.completed_at,
            )
            for cp in result["courses"]
        ],
        labs=[
            LabProgressResponse(
                id=lp.id,
                lab_slug=lp.lab_slug,
                status=lp.status,
                score=lp.score,
                current_step=lp.current_step,
                started_at=lp.started_at,
                completed_at=lp.completed_at,
            )
            for lp in result["labs"]
        ],
    )


@router.get("/labs/{lab_slug}", response_model=LabProgressDetailResponse)
async def get_lab_progress(
    lab_slug: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    detail = await get_lab_progress_detail(db, current_user["id"], lab_slug)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No progress found"
        )
    lp = detail["progress"]
    return LabProgressDetailResponse(
        id=lp.id,
        lab_slug=lp.lab_slug,
        status=lp.status,
        score=lp.score,
        current_step=lp.current_step,
        started_at=lp.started_at,
        completed_at=lp.completed_at,
        attempts=[
            StepAttemptResponse(
                id=a.id,
                step_slug=a.step_slug,
                attempt_number=a.attempt_number,
                result=a.result,
                score=a.score,
                started_at=a.started_at,
                ended_at=a.ended_at,
            )
            for a in detail["attempts"]
        ],
    )


@router.post("/labs/{lab_slug}/start", response_model=LabProgressResponse)
async def start_lab_endpoint(
    lab_slug: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lp = await start_lab(db, current_user["id"], lab_slug)
    return LabProgressResponse(
        id=lp.id,
        lab_slug=lp.lab_slug,
        status=lp.status,
        score=lp.score,
        current_step=lp.current_step,
        started_at=lp.started_at,
        completed_at=lp.completed_at,
    )


@router.post(
    "/labs/{lab_slug}/steps/{step_slug}/attempt",
    response_model=StepAttemptResponse,
)
async def record_attempt_endpoint(
    lab_slug: str,
    step_slug: str,
    body: StepAttemptCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    attempt = await record_step_attempt(
        db,
        current_user["id"],
        lab_slug,
        step_slug,
        result=body.result,
        score=body.score,
        error_details=body.error_details,
    )
    return StepAttemptResponse(
        id=attempt.id,
        step_slug=attempt.step_slug,
        attempt_number=attempt.attempt_number,
        result=attempt.result,
        score=attempt.score,
        started_at=attempt.started_at,
        ended_at=attempt.ended_at,
    )
