from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.progress import CourseProgress, LabProgress, StepAttempt


async def start_lab(db: AsyncSession, user_id: str, lab_slug: str) -> LabProgress:
    result = await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == user_id, LabProgress.lab_slug == lab_slug
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing
    lp = LabProgress(
        user_id=user_id,
        lab_slug=lab_slug,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db.add(lp)
    await db.commit()
    await db.refresh(lp)
    return lp


async def record_step_attempt(
    db: AsyncSession,
    user_id: str,
    lab_slug: str,
    step_slug: str,
    result: str,
    score: float | None = None,
    error_details: dict | None = None,
) -> StepAttempt:
    count_result = await db.execute(
        select(func.count()).where(
            StepAttempt.user_id == user_id,
            StepAttempt.lab_slug == lab_slug,
            StepAttempt.step_slug == step_slug,
        )
    )
    attempt_number = count_result.scalar() + 1
    attempt = StepAttempt(
        user_id=user_id,
        lab_slug=lab_slug,
        step_slug=step_slug,
        attempt_number=attempt_number,
        result=result,
        score=score,
        error_details=error_details,
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return attempt


async def get_all_progress(db: AsyncSession, user_id: str) -> dict:
    courses_result = await db.execute(
        select(CourseProgress).where(CourseProgress.user_id == user_id)
    )
    labs_result = await db.execute(
        select(LabProgress).where(LabProgress.user_id == user_id)
    )
    return {
        "courses": list(courses_result.scalars().all()),
        "labs": list(labs_result.scalars().all()),
    }


async def get_lab_progress_detail(
    db: AsyncSession, user_id: str, lab_slug: str
) -> dict | None:
    lp_result = await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == user_id, LabProgress.lab_slug == lab_slug
        )
    )
    progress = lp_result.scalar_one_or_none()
    if progress is None:
        return None
    attempts_result = await db.execute(
        select(StepAttempt)
        .where(StepAttempt.user_id == user_id, StepAttempt.lab_slug == lab_slug)
        .order_by(StepAttempt.step_slug, StepAttempt.attempt_number)
    )
    return {
        "progress": progress,
        "attempts": list(attempts_result.scalars().all()),
    }
