from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.progress import CourseProgress, LabProgress, StepAttempt


def score_from_steps(steps: list[dict]) -> tuple[float, bool]:
    """Оценка по доле пройденных проверок и флаг полного прохождения.

    Возвращает `(score, all_passed)`, где score = passed_checks / total_checks * 100,
    округлённое до целого. Если проверок нет — score 0.0. all_passed True, когда
    все шаги пройдены (используется для перевода лабы в статус completed.)
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
    """Обновить прогресс лабы по итогам прогона валидации.

    Оценка — доля пройденных проверок; берём лучшую из прежней и новой, чтобы
    неудачный повторный прогон не обнулял достижение. При полном прохождении лаба
    переводится в completed (необратимо в рамках последующих прогонов).
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
    """Возвращает существующий прогресс по лабораторной или создаёт новый со статусом in_progress."""
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
    """Создаёт попытку прохождения шага с автоматическим номером и сохраняет её в БД."""
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
    """Возвращает весь прогресс пользователя по курсам и лабораторным из БД."""
    courses_result = await db.execute(
        select(CourseProgress).where(CourseProgress.user_id == user_id)
    )
    labs_result = await db.execute(select(LabProgress).where(LabProgress.user_id == user_id))
    return {
        "courses": list(courses_result.scalars().all()),
        "labs": list(labs_result.scalars().all()),
    }


async def get_lab_progress_detail(db: AsyncSession, user_id: str, lab_slug: str) -> dict | None:
    """Возвращает прогресс по лабораторной с попытками по шагам или None, если прогресса нет."""
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
