from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from experiment.group_assigner import assign_group
from models.session import LearningSession
from models.user import User


async def create_session(
    db: AsyncSession, user_id: str, lab_slug: str
) -> LearningSession:
    await _assign_experiment_group_if_needed(db, user_id)
    session = LearningSession(user_id=user_id, lab_slug=lab_slug)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def _assign_experiment_group_if_needed(db: AsyncSession, user_id: str) -> None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is not None and user.experiment_group is None:
        user.experiment_group = assign_group().value


async def end_session(
    db: AsyncSession, session_id: str, user_id: str, status: str
) -> LearningSession | None:
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None
    session.status = status
    session.ended_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


async def get_user_sessions(db: AsyncSession, user_id: str) -> list[LearningSession]:
    result = await db.execute(
        select(LearningSession)
        .where(LearningSession.user_id == user_id)
        .order_by(LearningSession.started_at.desc())
    )
    return list(result.scalars().all())
