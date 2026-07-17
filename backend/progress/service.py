from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.progress import CourseProgress, LabProgress, StepAttempt


def score_from_steps(steps: list[dict]) -> tuple[float, bool]:
    """Score by the share of passed checks, plus a full-completion flag.

    Returns `(score, all_passed)`, where score = passed_checks / total_checks * 100,
    rounded to a whole number. Score is 0.0 if there are no checks. all_passed is True
    when all steps passed (used to move the lab to the completed status).
    """
    total = 0
    passed = 0
    for step in steps:
        for check in step.get("checks") or []:
            total += 1
            if check.get("ok"):
                passed += 1
    score = round(passed / total * 100, 1) if total else 0.0
    all_passed = bool(steps) and all(s.get("ok") for s in steps)
    return score, all_passed


async def record_lab_validation(
    db: AsyncSession, user_id: str, lab_slug: str, steps: list[dict]
) -> LabProgress:
    """Update lab progress from the results of a validation run.

    Score is the share of passed checks; we keep the best of the old and new score
    so a failed re-run doesn't wipe out prior achievement. On full completion, the
    lab moves to completed (irreversible across subsequent runs).
    """
    score, all_passed = score_from_steps(steps)
    now = datetime.now(UTC)

    result = await db.execute(
        select(LabProgress).where(LabProgress.user_id == user_id, LabProgress.lab_slug == lab_slug)
    )
    lp = result.scalar_one_or_none()
    if lp is None:
        lp = LabProgress(user_id=user_id, lab_slug=lab_slug, started_at=now)
        db.add(lp)

    if lp.started_at is None:
        lp.started_at = now
    lp.score = max(lp.score or 0.0, score)

    if all_passed:
        if lp.status != "completed":
            lp.status = "completed"
            lp.completed_at = now
    elif lp.status != "completed":
        lp.status = "in_progress"

    await db.commit()
    await db.refresh(lp)
    return lp


async def start_lab(db: AsyncSession, user_id: str, lab_slug: str) -> LabProgress:
    """Returns existing lab progress or creates a new one with status in_progress."""
    result = await db.execute(
        select(LabProgress).where(LabProgress.user_id == user_id, LabProgress.lab_slug == lab_slug)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing
    lp = LabProgress(
        user_id=user_id,
        lab_slug=lab_slug,
        status="in_progress",
        started_at=datetime.now(UTC),
    )
    db.add(lp)
    await db.flush()
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
    """Creates a step attempt with an auto-incremented number and saves it to the DB."""
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
    await db.flush()
    await db.refresh(attempt)
    return attempt


async def get_all_progress(db: AsyncSession, user_id: str) -> dict:
    """Returns all of the user's progress across courses and labs from the DB."""
    courses_result = await db.execute(
        select(CourseProgress).where(CourseProgress.user_id == user_id)
    )
    labs_result = await db.execute(select(LabProgress).where(LabProgress.user_id == user_id))
    return {
        "courses": list(courses_result.scalars().all()),
        "labs": list(labs_result.scalars().all()),
    }


async def get_lab_progress_detail(db: AsyncSession, user_id: str, lab_slug: str) -> dict | None:
    """Returns lab progress with step attempts, or None if there's no progress."""
    lp_result = await db.execute(
        select(LabProgress).where(LabProgress.user_id == user_id, LabProgress.lab_slug == lab_slug)
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
