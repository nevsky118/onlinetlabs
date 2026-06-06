"""Эндпоинты чтения: список сессий, детали, состояние, чат."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from chat.persistence import get_chat_history
from db.session import get_db
from deps import get_gns3_client, get_state_cache
from models.lab import Lab
from sessions.schemas import (
    ChatMessageResponse,
    FullSessionStateResponse,
    LearningSessionResponse,
)
from sessions.service import get_session, get_session_state, get_user_sessions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[LearningSessionResponse])
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает список всех учебных сессий текущего пользователя."""
    sessions = await get_user_sessions(db, current_user["id"])
    slugs = {s.lab_slug for s in sessions}
    titles: dict[str, str] = {}
    if slugs:
        rows = await db.execute(select(Lab.slug, Lab.title).where(Lab.slug.in_(slugs)))
        titles = dict(rows.all())
    return [
        LearningSessionResponse(
            id=s.id,
            lab_slug=s.lab_slug,
            lab_title=titles.get(s.lab_slug),
            status=s.status,
            started_at=s.started_at,
            ended_at=s.ended_at,
            meta=None,  # зашифрованные креды не отдаём в списке
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=LearningSessionResponse)
async def get_session_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает данные сессии по её идентификатору."""
    session = await get_session(db, session_id, current_user["id"])
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    lab = await db.get(Lab, session.lab_slug)
    return LearningSessionResponse(
        id=session.id,
        lab_slug=session.lab_slug,
        lab_title=lab.title if lab else None,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        meta=None,
    )


@router.get("/{session_id}/chat", response_model=list[ChatMessageResponse])
async def get_session_chat_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает историю сообщений чата сессии."""
    session = await get_session(db, session_id, current_user["id"])
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return await get_chat_history(db, session_id)


@router.get("/{session_id}/state", response_model=FullSessionStateResponse)
async def get_state_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
    state_cache=Depends(get_state_cache),
):
    """Возвращает полное текущее состояние сессии с топологией GNS3."""
    state = await get_session_state(db, session_id, current_user["id"], gns3_client, state_cache)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return state
