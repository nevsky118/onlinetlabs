"""#8: help-dependence -- dynamics of learner-initiated help requests.

Secondary-endpoint MRT: declining reliance on help across sessions = a learning
signal (unlike in-session success, which copilots deliver too).
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat_message import ChatMessage


async def help_dependence_count(db: AsyncSession, session_id: str) -> int:
    """Count of learner-initiated help requests (ChatMessage role=user) in a session."""
    return (await db.execute(
        select(func.count()).select_from(ChatMessage).where(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user",
        )
    )).scalar_one()


async def help_dependence_trajectory(db: AsyncSession, session_ids: list[str]) -> list[int]:
    """Help-reliance counts across sessions, in the given order."""
    return [await help_dependence_count(db, sid) for sid in session_ids]


def is_declining(counts: list[int]) -> bool:
    """Help reliance is declining: last point below the first (needs >=2 points)."""
    return len(counts) >= 2 and counts[-1] < counts[0]
