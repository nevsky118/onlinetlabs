"""Session state-change endpoints for launch, stop, restart, reset, end, and node actions."""

import logging
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, status
from fastapi import Request as FastAPIRequest
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_active_user
from clients.mcp import MCPToolError
from consent.consent import study_decision
from i18n import Locale, LocalizedError
from kit.db import get_db, get_db_factory
from kit.deps import (
    get_gns3_client,
    get_locale,
    get_mcp_client,
    get_monitor_registry,
    get_state_cache,
)
from kit.rate_limit import limiter
from observability.metrics import active_sessions_gauge
from sessions.activity import touch_path_session
from sessions.context import build_session_context
from sessions.monitor_registry import SessionMonitorRegistry
from sessions.queue import SessionQueueService, get_queue_service
from sessions.schemas import (
    LaunchResponse,
    LearningSessionCreate,
    OkResponse,
)
from sessions.service import (
    end_lab,
    get_active_session,
    launch_session,
    proxy_bulk_node_action,
    proxy_node_action,
    reset_lab,
    restart_lab,
    stop_lab,
)
from sessions.services.proxy import get_bulk_semaphore

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users/me/sessions",
    tags=["sessions"],
    dependencies=[Depends(touch_path_session)],
)

BackendNodeAction = Literal["start", "stop", "suspend", "reload"]


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("2000/minute")
async def launch_endpoint(
    request: FastAPIRequest,
    body: LearningSessionCreate,
    current_user: dict = Depends(get_current_user),
    _active: dict = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
    db_factory=Depends(get_db_factory),
    gns3_client=Depends(get_gns3_client),
    monitor_registry: SessionMonitorRegistry = Depends(get_monitor_registry),
    queue: SessionQueueService = Depends(get_queue_service),
    locale: Locale = Depends(get_locale),
):
    """Launches a lab and creates a session, issuing GNS3 credentials.

    If there are no free slots, puts the user in the queue and returns their position.
    """
    # Push user_id and lab_slug into structlog contextvars so all subsequent
    # logs within this request automatically carry these fields.
    structlog.contextvars.bind_contextvars(user_id=current_user["id"], lab_slug=body.lab_slug)
    # asked before the session exists, so the observer cannot write first
    if await study_decision(db, current_user["id"]) is None:
        raise LocalizedError("error.consent.required", status_code=428)
    # Relaunching an already-active session must not take a queue slot or
    # double-count it; slot/monitoring/gauge are only touched for a new launch.
    existing = await get_active_session(db, current_user["id"], body.lab_slug)
    is_new_launch = existing is None

    if is_new_launch:
        acquired = await queue.try_acquire(current_user["id"], body.lab_slug)
        if not acquired:
            pos = await queue.enqueue(current_user["id"], body.lab_slug)
            depth = await queue.queue_depth(body.lab_slug)
            eta_sec = round(depth * await queue.avg_provision_seconds())
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "status": "queued",
                    "queue_position": pos,
                    "queue_depth": depth,
                    "eta_sec": eta_sec,
                    "lab_slug": body.lab_slug,
                },
            )
    try:
        session, creds = await launch_session(
            db, current_user["id"], body.lab_slug, gns3_client, db_factory=db_factory, locale=locale
        )
    except LocalizedError:
        if is_new_launch:
            await queue.release(body.lab_slug)
        raise
    except Exception:
        if is_new_launch:
            await queue.release(body.lab_slug)
        raise LocalizedError("error.session.provisioning_failed", status_code=502)
    structlog.contextvars.bind_contextvars(session_id=session.id)
    if is_new_launch and session.status == "active":
        ctx = build_session_context(session)
        await monitor_registry.start(session.id, session.user_id, session.lab_slug, ctx)

        active_sessions_gauge.labels(lab_slug=body.lab_slug).inc()
    return LaunchResponse(
        session_id=session.id,
        status=session.status,
        gns3_username=creds["gns3_username"],
        gns3_url=creds["gns3_url"],
        gns3_deep_url=creds["gns3_deep_url"],
    )


@router.post("/{session_id}/stop", response_model=OkResponse)
async def stop_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    mcp_client=Depends(get_mcp_client),
    gns3_client=Depends(get_gns3_client),
):
    """Stops the lab within the session."""
    try:
        ok = await stop_lab(db, session_id, current_user["id"], mcp_client, gns3_client)
    except MCPToolError as exc:
        raise LocalizedError("error.session.gns3_operation_failed", status_code=502, error=str(exc))
    if not ok:
        raise LocalizedError("error.session.not_found", status_code=404)
    return {"ok": True}


@router.post("/{session_id}/restart", response_model=OkResponse)
async def restart_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    mcp_client=Depends(get_mcp_client),
    gns3_client=Depends(get_gns3_client),
):
    """Restarts the lab within the session."""
    try:
        ok = await restart_lab(db, session_id, current_user["id"], mcp_client, gns3_client)
    except MCPToolError as exc:
        raise LocalizedError("error.session.gns3_operation_failed", status_code=502, error=str(exc))
    if not ok:
        raise LocalizedError("error.session.not_found", status_code=404)
    return {"ok": True}


@router.post("/{session_id}/reset", response_model=OkResponse)
async def reset_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
):
    """Resets the lab to its initial state within the session."""
    if not await reset_lab(db, session_id, current_user["id"], gns3_client):
        raise LocalizedError("error.session.not_found", status_code=404)
    return {"ok": True}


@router.post("/{session_id}/end", response_model=OkResponse)
async def end_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
    monitor_registry: SessionMonitorRegistry = Depends(get_monitor_registry),
):
    """Ends the session and releases GNS3 resources."""
    if not await end_lab(db, session_id, current_user["id"], gns3_client, monitor_registry):
        raise LocalizedError("error.session.not_found", status_code=404)
    return {"ok": True}


@router.post("/{session_id}/nodes/{node_id}/{action}", response_model=OkResponse)
@limiter.limit("5/second")
async def node_action_endpoint(
    request: FastAPIRequest,
    session_id: str,
    node_id: str,
    action: BackendNodeAction,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
    state_cache=Depends(get_state_cache),
):
    """Performs an action on a topology node (start, stop, suspend, reload)."""
    ok = await proxy_node_action(
        db,
        session_id,
        current_user["id"],
        node_id,
        action,
        gns3_client,
        state_cache,
    )
    if not ok:
        raise LocalizedError("error.session.not_found", status_code=404)
    return {"ok": True}


@router.post("/{session_id}/nodes/{action}", response_model=OkResponse)
@limiter.limit("5/second")
async def bulk_node_action_endpoint(
    request: FastAPIRequest,
    session_id: str,
    action: BackendNodeAction,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
    state_cache=Depends(get_state_cache),
    bulk_semaphore=Depends(get_bulk_semaphore),
):
    """Performs an action on all topology nodes of the session at once."""
    ok = await proxy_bulk_node_action(
        db,
        session_id,
        current_user["id"],
        action,
        gns3_client,
        state_cache,
        semaphore=bulk_semaphore,
    )
    if not ok:
        raise LocalizedError("error.session.not_found", status_code=404)
    return {"ok": True}
