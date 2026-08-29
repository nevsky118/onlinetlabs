"""Session read endpoints for listing, details, state, chat, credentials, activity, and queue status.

`/queue-status` must stay registered before the catch-all `/{session_id}`:
Starlette matches in registration order.

`agent_activity_router` is deliberately separate and mounted by main.py under
`/sessions`, not `/users/me/sessions`. The frontend calls
`/sessions/{session_id}/agent-activity`, so folding it into `router` would
change the path and break that caller.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import can_view_session_activity, get_current_user
from chat.persistence import get_chat_history
from i18n import Locale, LocalizedError, resolve_localized
from kit.db import get_db
from kit.deps import get_activity_log, get_gns3_client, get_locale, get_state_cache
from models.catalog import Lab
from models.learning import LearningSession
from observability.schemas import AgentActivityEvent
from sessions.activity import touch_path_session
from sessions.queue import SessionQueueService, get_queue_service
from sessions.schemas import (
    ActivityResponseSchema,
    ChatMessageResponse,
    CredentialsResponse,
    FullSessionStateResponse,
    LearningSessionResponse,
    QueueStatusResponse,
)
from sessions.service import (
    get_credentials,
    get_session,
    get_session_state,
    get_user_sessions,
    proxy_activity,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users/me/sessions",
    tags=["sessions"],
    dependencies=[Depends(touch_path_session)],
)


@router.get("", response_model=list[LearningSessionResponse])
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    locale: Locale = Depends(get_locale),
):
    """Returns the list of all learning sessions of the current user."""
    sessions = await get_user_sessions(db, current_user["id"])
    slugs = {s.lab_slug for s in sessions}
    titles: dict[str, str] = {}
    if slugs:
        rows = await db.execute(select(Lab.slug, Lab.title_i18n).where(Lab.slug.in_(slugs)))
        titles = {slug: resolve_localized(title_i18n, locale) for slug, title_i18n in rows.all()}
    return [
        LearningSessionResponse(
            id=s.id,
            lab_slug=s.lab_slug,
            lab_title=titles.get(s.lab_slug),
            status=s.status,
            started_at=s.started_at,
            ended_at=s.ended_at,
            meta=None,  # don't expose encrypted credentials in the list
        )
        for s in sessions
    ]


@router.get("/queue-status", response_model=QueueStatusResponse, response_model_exclude_none=True)
async def queue_status(
    lab_slug: str,
    current_user: dict = Depends(get_current_user),
    queue: SessionQueueService = Depends(get_queue_service),
):
    """Returns the user's position in the lab queue and its depth."""
    pos = await queue.position(current_user["id"], lab_slug)
    depth = await queue.queue_depth(lab_slug)
    if pos is None:
        return {"in_queue": False, "queue_depth": depth}
    return {
        "in_queue": True,
        "queue_position": pos,
        "queue_depth": depth,
        "eta_sec": round(pos * await queue.avg_provision_seconds()),
    }


@router.get("/{session_id}", response_model=LearningSessionResponse)
async def get_session_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    locale: Locale = Depends(get_locale),
):
    """Returns session data by its identifier."""
    session = await get_session(db, session_id, current_user["id"])
    if session is None:
        raise LocalizedError("error.session.not_found", status_code=404)
    lab = await db.get(Lab, session.lab_slug)
    return LearningSessionResponse(
        id=session.id,
        lab_slug=session.lab_slug,
        lab_title=resolve_localized(lab.title_i18n, locale) if lab else None,
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
    """Returns the session's chat message history."""
    session = await get_session(db, session_id, current_user["id"])
    if session is None:
        raise LocalizedError("error.session.not_found", status_code=404)
    return await get_chat_history(db, session_id)


@router.get("/{session_id}/state", response_model=FullSessionStateResponse)
async def get_state_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
    state_cache=Depends(get_state_cache),
    locale: Locale = Depends(get_locale),
):
    """Returns the full current session state with GNS3 topology."""
    state = await get_session_state(
        db, session_id, current_user["id"], gns3_client, state_cache, locale
    )
    if state is None:
        raise LocalizedError("error.session.not_found", status_code=404)
    return state


@router.get("/{session_id}/credentials", response_model=CredentialsResponse)
async def credentials_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns GNS3 access credentials for the session."""
    creds = await get_credentials(db, session_id, current_user["id"])
    if creds is None:
        raise LocalizedError("error.session.not_found", status_code=404)
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
    """Returns the session activity feed with cursor-based pagination."""
    result = await proxy_activity(
        db,
        session_id,
        current_user["id"],
        limit,
        cursor,
        gns3_client,
    )
    if result is None:
        raise LocalizedError("error.session.not_found", status_code=404)
    return result


# agent_activity_router is mounted separately; see the module docstring above.

agent_activity_router = APIRouter(prefix="/sessions", tags=["observability"])


@agent_activity_router.get("/{session_id}/agent-activity", response_model=list[AgentActivityEvent])
async def get_agent_activity(
    session_id: str,
    since: datetime | None = None,
    limit: int = 200,
    current_user: dict = Depends(get_current_user),
    activity=Depends(get_activity_log),
    db: AsyncSession = Depends(get_db),
):
    """Agent activity event history for the session (instructor/admin or owner)."""
    session = await db.get(LearningSession, session_id)
    if session is None:
        raise LocalizedError("error.session.not_found", status_code=404)
    if not can_view_session_activity(current_user, session):
        raise LocalizedError("error.session.forbidden", status_code=403)
    # cap history size to avoid DoS
    limit = max(1, min(limit, 1000))
    return await activity.history(session_id, since, limit)
