"""Session read endpoints for listing, details, state, chat, credentials, activity, and queue status.

`/queue-status` is registered BEFORE the catch-all `/{session_id}` in this
same file. Otherwise the `{session_id}` route would swallow the literal
path (Starlette matches routes in registration order).

`agent_activity_router` is a separate APIRouter, NOT included in `router`
below. In main.py it's mounted with a separate include_router under the
`/sessions` prefix (not `/users/me/sessions` like everything else here);
that was the case even before the router consolidation. Folding it into
the shared `router` would change the resulting path to
`/users/me/sessions/{session_id}/agent-activity` and break the real
consumer (the frontend hits `/sessions/{session_id}/agent-activity`
directly), so the handler code was moved here, but its registration was
not.
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
    """Returns the list of all learning sessions of the current user."""
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
            meta=None,  # don't expose encrypted credentials in the list
        )
        for s in sessions
    ]


@router.get("/queue-status")
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
        "eta_sec": pos * QUEUE_AVG_PROVISION_SEC,
    }


@router.get("/{session_id}", response_model=LearningSessionResponse)
async def get_session_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns session data by its identifier."""
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
    """Returns the session's chat message history."""
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
    """Returns the full current session state with GNS3 topology."""
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
    """Returns GNS3 access credentials for the session."""
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
        raise HTTPException(status_code=404, detail="Session not found")
    return result


# agent_activity_router is mounted separately; see the module docstring above.

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
    """Agent activity event history for the session (instructor/admin or owner)."""
    session = await db.get(LearningSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not can_view_session_activity(current_user, session):
        raise HTTPException(status_code=403, detail="Forbidden")
    # cap history size to avoid DoS
    limit = max(1, min(limit, 1000))
    return await activity.history(session_id, since, limit)
