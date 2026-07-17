"""#8: help-dependence — динамика learner-инициированных запросов помощи.

Secondary-endpoint MRT: снижение опоры на помощь между сессиями = признак обучения
(в отличие от in-session success, который дают и копайлоты).
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat_message import ChatMessage


async def help_dependence_count(db: AsyncSession, session_id: str) -> int:
    """Число learner-инициированных запросов помощи (ChatMessage role=user) в сессии."""
    return (await db.execute(
        select(func.count()).select_from(ChatMessage).where(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user",
        )
    )).scalar_one()


async def help_dependence_trajectory(db: AsyncSession, session_ids: list[str]) -> list[int]:
    """Счётчики опоры на помощь по сессиям в заданном порядке."""
    return [await help_dependence_count(db, sid) for sid in session_ids]


def is_declining(counts: list[int]) -> bool:
    """Опора на помощь снижается: последняя точка ниже первой (нужно >=2 точки)."""
    return len(counts) >= 2 and counts[-1] < counts[0]
