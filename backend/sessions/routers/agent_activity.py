"""REST-эндпоинт истории активности агентов для сессии."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import can_view_session_activity, get_current_user
from db.session import get_db
from deps import get_activity_log
from models.session import LearningSession

router = APIRouter()


@router.get("/{session_id}/agent-activity")
async def get_agent_activity(
    session_id: str,
    since: datetime | None = None,
    limit: int = 200,
    current_user: dict = Depends(get_current_user),
    activity=Depends(get_activity_log),
    db: AsyncSession = Depends(get_db),
):
    """История событий активности агентов для сессии (препод/админ или владелец)."""
    session = await db.get(LearningSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not can_view_session_activity(current_user, session):
        raise HTTPException(status_code=403, detail="Forbidden")
    # ограничить размер истории чтобы избежать DoS
    limit = max(1, min(limit, 1000))
    return await activity.history(session_id, since, limit)
