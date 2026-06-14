"""Запросы для кабинета преподавателя.

Подсказки считаются как поведенческие события с event_type='intervention' —
именно так монитор учебной сессии логирует выданные ученику интервенции
(см. learning_analytics/monitor.py).
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.behavioral_event import BehavioralEvent
from models.lab import Lab
from models.progress import LabProgress, StepAttempt
from models.session import LearningSession
from models.user import User

HINT_EVENT_TYPE = "intervention"


def _avg(scores: list[float]) -> float | None:
    """Среднее по непустому списку оценок, иначе None."""
    return round(sum(scores) / len(scores), 2) if scores else None


async def get_students_overview(db: AsyncSession) -> dict:
    """Сводка по всем ученикам: прогресс, подсказки, сессии, активность.

    Считает агрегаты пачкой group by, а не запросом на ученика, чтобы
    таблица кабинета масштабировалась на десятки-сотни учеников.
    """
    students_result = await db.execute(
        select(User).where(User.role == "student").order_by(User.name, User.email)
    )
    students = list(students_result.scalars().all())
    if not students:
        return {"students": [], "total_students": 0, "total_hints": 0}

    user_ids = [s.id for s in students]

    # Прогресс по лабам: статусы и оценки на ученика
    progress_result = await db.execute(
        select(
            LabProgress.user_id, LabProgress.status, LabProgress.score
        ).where(LabProgress.user_id.in_(user_ids))
    )
    completed: dict[str, int] = {}
    in_progress: dict[str, int] = {}
    total_labs: dict[str, int] = {}
    scores: dict[str, list[float]] = {}
    for user_id, p_status, score in progress_result.all():
        total_labs[user_id] = total_labs.get(user_id, 0) + 1
        if p_status == "completed":
            completed[user_id] = completed.get(user_id, 0) + 1
        elif p_status == "in_progress":
            in_progress[user_id] = in_progress.get(user_id, 0) + 1
        if score is not None:
            scores.setdefault(user_id, []).append(score)

    # Подсказки на ученика
    hints_result = await db.execute(
        select(BehavioralEvent.user_id, func.count())
        .where(
            BehavioralEvent.user_id.in_(user_ids),
            BehavioralEvent.event_type == HINT_EVENT_TYPE,
        )
        .group_by(BehavioralEvent.user_id)
    )
    hints = {user_id: count for user_id, count in hints_result.all()}

    # Сессии и последняя активность на ученика
    sessions_result = await db.execute(
        select(
            LearningSession.user_id,
            func.count(),
            func.max(LearningSession.started_at),
        )
        .where(LearningSession.user_id.in_(user_ids))
        .group_by(LearningSession.user_id)
    )
    sessions: dict[str, int] = {}
    last_active: dict[str, object] = {}
    for user_id, count, last_started in sessions_result.all():
        sessions[user_id] = count
        last_active[user_id] = last_started

    overview = [
        {
            "user_id": s.id,
            "name": s.name,
            "email": s.email,
            "labs_total": total_labs.get(s.id, 0),
            "labs_completed": completed.get(s.id, 0),
            "labs_in_progress": in_progress.get(s.id, 0),
            "avg_score": _avg(scores.get(s.id, [])),
            "total_hints": hints.get(s.id, 0),
            "total_sessions": sessions.get(s.id, 0),
            "last_active_at": last_active.get(s.id),
        }
        for s in students
    ]
    return {
        "students": overview,
        "total_students": len(students),
        "total_hints": sum(hints.values()),
    }


async def get_student_detail(db: AsyncSession, user_id: str) -> dict | None:
    """Детальная карточка ученика с разбивкой по лабам или None, если ученика нет."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return None

    progress_result = await db.execute(
        select(LabProgress)
        .where(LabProgress.user_id == user_id)
        .order_by(LabProgress.updated_at.desc())
    )
    progress_rows = list(progress_result.scalars().all())

    # Подсказки по лабам
    hints_result = await db.execute(
        select(BehavioralEvent.lab_slug, func.count())
        .where(
            BehavioralEvent.user_id == user_id,
            BehavioralEvent.event_type == HINT_EVENT_TYPE,
        )
        .group_by(BehavioralEvent.lab_slug)
    )
    hints_by_lab = {lab_slug: count for lab_slug, count in hints_result.all()}

    # Сессии и последняя активность по лабам
    sessions_result = await db.execute(
        select(
            LearningSession.lab_slug,
            func.count(),
            func.max(LearningSession.started_at),
        )
        .where(LearningSession.user_id == user_id)
        .group_by(LearningSession.lab_slug)
    )
    sessions_by_lab: dict[str, int] = {}
    last_active_by_lab: dict[str, object] = {}
    for lab_slug, count, last_started in sessions_result.all():
        sessions_by_lab[lab_slug] = count
        last_active_by_lab[lab_slug] = last_started

    # Попытки по шагам, сгруппированные по лабам
    attempts_result = await db.execute(
        select(StepAttempt.lab_slug, func.count())
        .where(StepAttempt.user_id == user_id)
        .group_by(StepAttempt.lab_slug)
    )
    attempts_by_lab = {lab_slug: count for lab_slug, count in attempts_result.all()}

    # Названия лаб
    lab_slugs = {p.lab_slug for p in progress_rows}
    titles: dict[str, str] = {}
    if lab_slugs:
        titles_result = await db.execute(
            select(Lab.slug, Lab.title).where(Lab.slug.in_(lab_slugs))
        )
        titles = {slug: title for slug, title in titles_result.all()}

    labs = [
        {
            "lab_slug": p.lab_slug,
            "lab_title": titles.get(p.lab_slug, p.lab_slug),
            "status": p.status,
            "score": p.score,
            "current_step": p.current_step,
            "hints": hints_by_lab.get(p.lab_slug, 0),
            "sessions": sessions_by_lab.get(p.lab_slug, 0),
            "attempts": attempts_by_lab.get(p.lab_slug, 0),
            "started_at": p.started_at,
            "completed_at": p.completed_at,
            "last_active_at": last_active_by_lab.get(p.lab_slug),
        }
        for p in progress_rows
    ]

    completed = sum(1 for p in progress_rows if p.status == "completed")
    in_progress = sum(1 for p in progress_rows if p.status == "in_progress")
    scores = [p.score for p in progress_rows if p.score is not None]

    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "labs_completed": completed,
        "labs_in_progress": in_progress,
        "avg_score": _avg(scores),
        "total_hints": sum(hints_by_lab.values()),
        "total_sessions": sum(sessions_by_lab.values()),
        "labs": labs,
    }
