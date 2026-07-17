from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from progress.schemas import (
    AllProgressResponse,
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
    """Returns all of the user's progress across courses and labs."""
    result = await get_all_progress(db, current_user["id"])
    return AllProgressResponse(courses=result["courses"], labs=result["labs"])


@router.get("/labs/{lab_slug}", response_model=LabProgressDetailResponse)
async def get_lab_progress(
    lab_slug: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns lab progress with step attempts.

    Returns 404 if there's no progress.
    """
    detail = await get_lab_progress_detail(db, current_user["id"], lab_slug)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No progress found")
    lp = detail["progress"]
    lp.attempts = detail["attempts"]
    return lp


@router.post("/labs/{lab_slug}/start", response_model=LabProgressResponse)
async def start_lab_endpoint(
    lab_slug: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Starts the lab for the user and returns its progress."""
    return await start_lab(db, current_user["id"], lab_slug)


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
    """Records a lab step attempt."""
    return await record_step_attempt(
        db,
        current_user["id"],
        lab_slug,
        step_slug,
        result=body.result,
        score=body.score,
        error_details=body.error_details,
    )
