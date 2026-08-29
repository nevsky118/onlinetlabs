"""Row lookups for learning sessions. Reads only, no side effects."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.learning import LearningSession


async def get_user_sessions(db: AsyncSession, user_id: str) -> list[LearningSession]:
    """Returns all user sessions from newest to oldest."""
    result = await db.execute(
        select(LearningSession)
        .where(LearningSession.user_id == user_id)
        .order_by(LearningSession.started_at.desc())
    )
    return list(result.scalars().all())


async def get_active_session(db, user_id: str, lab_slug: str):
    """Returns the user's active session for the given lab, if any."""
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.user_id == user_id,
            LearningSession.lab_slug == lab_slug,
            LearningSession.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def get_owned_session(db, session_id: str, user_id: str):
    """Returns the session, verifying it belongs to the user."""
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_session(db, session_id: str, user_id: str) -> LearningSession | None:
    """Returns the user's session by identifier."""
    return await get_owned_session(db, session_id, user_id)
