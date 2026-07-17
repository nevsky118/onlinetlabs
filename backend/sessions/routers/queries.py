"""Эндпоинты чтения сессии: список, детали, состояние, чат, креды, активность, очередь.

`/queue-status` регистрируется РАНЬШЕ catch-all `/{session_id}` в этом же
файле — иначе `{session_id}`-роут проглотил бы литеральный путь (Starlette
матчит маршруты в порядке регистрации).

`agent_activity_router` — отдельный APIRouter, НЕ включённый в `router` ниже.
В main.py он монтируется отдельным include_router с префиксом `/sessions`
(а не `/users/me/sessions`, как всё остальное здесь) — так было и до
консолидации роутеров. Смешение его в общий `router` изменило бы итоговый
путь на `/users/me/sessions/{session_id}/agent-activity` и сломало бы
реального потребителя (frontend дергает `/sessions/{session_id}/agent-activity`
напрямую), поэтому код хендлера перенесён сюда, а регистрация — нет.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import can_view_session_activity, get_current_user
from chat.persistence import get_chat_history
from db.session import get_db
from deps import get_activity_log, get_gns3_client, get_state_cache
from models.lab import Lab
from models.session import LearningSession
from sessions.queue import QUEUE_AVG_PROVISION_SEC, SessionQueueService, get_queue_service
from sessions.schemas import (
    ActivityResponseSchema,
    ChatMessageResponse,
    CredentialsResponse,
    FullSessionStateResponse,
    LearningSessionResponse,
)
from sessions.service import (
    get_credentials,
    get_session,
    get_session_state,
    get_user_sessions,
    proxy_activity,
)

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


@router.get("/queue-status")
async def queue_status(
    lab_slug: str,
    current_user: dict = Depends(get_current_user),
    queue: SessionQueueService = Depends(get_queue_service),
):
    """Возвращает позицию пользователя в очереди на лабу и её глубину."""
    pos = await queue.position(current_user["id"], lab_slug)
    depth = await queue.queue_depth(lab_slug)
    if pos is None:
        return {"in_queue": False, "queue_depth": depth}
    return {
        "in_queue": True,
        "queue_position": pos,
        "queue_depth": depth,
        "eta_sec": pos * QUEUE_AVG_PROVISION_SEC,
    }


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


@router.get("/{session_id}/credentials", response_model=CredentialsResponse)
async def credentials_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает учётные данные доступа к GNS3 для сессии."""
    creds = await get_credentials(db, session_id, current_user["id"])
    if creds is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return CredentialsResponse(**creds)


@router.get("/{session_id}/activity", response_model=ActivityResponseSchema)
async def get_activity_endpoint(
    session_id: str,
    limit: int = 50,
    cursor: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
):
    """Возвращает ленту активности сессии с постраничной навигацией по курсору."""
    result = await proxy_activity(
        db,
        session_id,
        current_user["id"],
        limit,
        cursor,
        gns3_client,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


# ── agent_activity: отдельный роутер, монтируется отдельно (см. docstring выше) ──

agent_activity_router = APIRouter()


@agent_activity_router.get("/{session_id}/agent-activity")
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
