from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.session import LearningSession


async def create_session(
    db: AsyncSession, user_id: str, lab_slug: str
) -> LearningSession:
    session = LearningSession(user_id=user_id, lab_slug=lab_slug)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


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
