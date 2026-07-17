"""Queries for the instructor dashboard.

Hints are counted as behavioral events with event_type='intervention' —
that's how the learning session monitor logs interventions delivered to the
student (see learning_analytics/monitor.py).
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.behavioral_event import BehavioralEvent
from models.chat_message import ChatMessage
from models.lab import Lab
from models.progress import LabProgress, StepAttempt
from models.session import LearningSession
from models.user import User

HINT_EVENT_TYPE = "intervention"


def _avg(scores: list[float]) -> float | None:
    """Average over a non-empty list of scores, else None."""
    return round(sum(scores) / len(scores), 2) if scores else None


async def get_students_overview(db: AsyncSession) -> dict:
    """Overview of all students: progress, hints, sessions, activity.

    Computes aggregates with a batched group by rather than one query per
    student, so the dashboard table scales to dozens-to-hundreds of students.
    """
    students_result = await db.execute(
        select(User).where(User.role == "student").order_by(User.name, User.email)
    )
    students = list(students_result.scalars().all())
    if not students:
        return {"students": [], "total_students": 0, "total_hints": 0}

    user_ids = [s.id for s in students]

    # Lab progress: statuses and scores per student
    progress_result = await db.execute(
        select(LabProgress.user_id, LabProgress.status, LabProgress.score).where(
            LabProgress.user_id.in_(user_ids)
        )
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

    # Hints per student
    hints_result = await db.execute(
        select(BehavioralEvent.user_id, func.count())
        .where(
            BehavioralEvent.user_id.in_(user_ids),
            BehavioralEvent.event_type == HINT_EVENT_TYPE,
        )
        .group_by(BehavioralEvent.user_id)
    )
    hints = {user_id: count for user_id, count in hints_result.all()}

    # Sessions and last activity per student
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
    """Detailed student card broken down by lab, or None if the student doesn't exist."""
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

    # Hints per lab
    hints_result = await db.execute(
        select(BehavioralEvent.lab_slug, func.count())
        .where(
            BehavioralEvent.user_id == user_id,
            BehavioralEvent.event_type == HINT_EVENT_TYPE,
        )
        .group_by(BehavioralEvent.lab_slug)
    )
    hints_by_lab = {lab_slug: count for lab_slug, count in hints_result.all()}

    # Sessions and last activity per lab
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

    # Step attempts grouped by lab
    attempts_result = await db.execute(
        select(StepAttempt.lab_slug, func.count())
        .where(StepAttempt.user_id == user_id)
        .group_by(StepAttempt.lab_slug)
    )
    attempts_by_lab = {lab_slug: count for lab_slug, count in attempts_result.all()}

    # Message counts per session
    msg_counts_result = await db.execute(
        select(ChatMessage.session_id, func.count())
        .join(LearningSession, ChatMessage.session_id == LearningSession.id)
        .where(LearningSession.user_id == user_id)
        .group_by(ChatMessage.session_id)
    )
    msg_counts = {sid: c for sid, c in msg_counts_result.all()}

    # Hints per session
    hint_counts_result = await db.execute(
        select(BehavioralEvent.session_id, func.count())
        .where(BehavioralEvent.user_id == user_id, BehavioralEvent.event_type == HINT_EVENT_TYPE)
        .group_by(BehavioralEvent.session_id)
    )
    hint_counts = {sid: c for sid, c in hint_counts_result.all()}

    # The sessions themselves (desc)
    session_rows_result = await db.execute(
        select(LearningSession)
        .where(LearningSession.user_id == user_id)
        .order_by(LearningSession.started_at.desc())
    )
    session_rows = list(session_rows_result.scalars().all())

    # Lab titles — extend with slugs from sessions
    lab_slugs = {p.lab_slug for p in progress_rows} | {s.lab_slug for s in session_rows}
    titles: dict[str, str] = {}
    if lab_slugs:
        titles_result = await db.execute(select(Lab.slug, Lab.title).where(Lab.slug.in_(lab_slugs)))
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

    sessions = [
        {
            "session_id": s.id,
            "lab_slug": s.lab_slug,
            "lab_title": titles.get(s.lab_slug, s.lab_slug),
            "status": s.status,
            "started_at": s.started_at,
            "ended_at": s.ended_at,
            "message_count": msg_counts.get(s.id, 0),
            "hint_count": hint_counts.get(s.id, 0),
        }
        for s in session_rows
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
        "sessions": sessions,
    }


async def build_session_timeline(db: AsyncSession, session_id: str) -> list[dict]:
    """Merge chat messages and session interventions into one timeline by time."""
    items: list[dict] = []

    msgs = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id))
    for m in msgs.scalars().all():
        items.append(
            {
                "kind": "student" if m.role == "user" else "tutor",
                "ts": m.created_at,
                "parts": m.parts,
            }
        )

    evs = await db.execute(
        select(BehavioralEvent).where(
            BehavioralEvent.session_id == session_id,
            BehavioralEvent.event_type == HINT_EVENT_TYPE,
        )
    )
    for e in evs.scalars().all():
        ed = e.extra_data or {}
        items.append(
            {
                "kind": "intervention",
                "ts": e.timestamp,
                "text": e.message,
                "action": e.action,
                "severity": e.severity,
                "hint_level": ed.get("hint_level"),
                "struggle_type": ed.get("struggle_type"),
            }
        )

    items.sort(key=lambda x: x["ts"])
    return items
