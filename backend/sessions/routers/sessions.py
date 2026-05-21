import logging

from fastapi import APIRouter, Depends, HTTPException, status
from chat.persistence import get_chat_history
from fastapi import Request as FastAPIRequest
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db, get_db_factory
from deps import get_gns3_client, get_mcp_client, get_monitor_registry, get_state_cache
from mcp_client.client import MCPToolError
from models.lab import Lab
from rate_limit import limiter
from sessions.context import build_session_context
from sessions.monitor_registry import SessionMonitorRegistry
from sessions.queue import SessionQueueService, get_queue_service
from sessions.schemas import (
    ChatMessageResponse,
    FullSessionStateResponse,
    LaunchResponse,
    LearningSessionCreate,
    LearningSessionResponse,
    LearningSessionUpdate,
)
from sessions.service import (
    end_lab,
    end_session,
    get_session,
    get_session_state,
    get_user_sessions,
    launch_session,
    reset_lab,
    restart_lab,
    stop_lab,
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
    return [
        LearningSessionResponse(
            id=s.id,
            lab_slug=s.lab_slug,
            status=s.status,
            started_at=s.started_at,
            ended_at=s.ended_at,
            meta=s.meta,
        )
        for s in sessions
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("2000/minute")
async def launch_endpoint(
    request: FastAPIRequest,
    body: LearningSessionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    db_factory=Depends(get_db_factory),
    gns3_client=Depends(get_gns3_client),
    monitor_registry: SessionMonitorRegistry = Depends(get_monitor_registry),
    queue: SessionQueueService = Depends(get_queue_service),
):
    """Запускает лабу и создаёт сессию с выдачей доступов к GNS3.

    Если свободных слотов нет, ставит пользователя в очередь и возвращает её позицию.
    """
    acquired = await queue.try_acquire(current_user["id"], body.lab_slug)
    if not acquired:
        pos = await queue.enqueue(current_user["id"], body.lab_slug)
        depth = await queue.queue_depth(body.lab_slug)
        eta_sec = depth * 30
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
            db, current_user["id"], body.lab_slug, gns3_client, db_factory=db_factory
        )
    except ValueError as exc:
        await queue.release(body.lab_slug)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        await queue.release(body.lab_slug)
        raise HTTPException(status_code=502, detail="GNS3 provisioning failed")
    if session.status == "active":
        ctx = build_session_context(session)
        await monitor_registry.start(session.id, session.user_id, session.lab_slug, ctx)
        from observability.metrics import active_sessions_gauge
        active_sessions_gauge.labels(lab_slug=body.lab_slug).inc()
    return LaunchResponse(
        session_id=session.id,
        status=session.status,
        gns3_username=creds["gns3_username"],
        gns3_password=creds["gns3_password"],
        gns3_url=creds["gns3_url"],
        gns3_deep_url=creds["gns3_deep_url"],
    )


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
        "eta_sec": pos * 30,
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


@router.post("/{session_id}/stop")
async def stop_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    mcp_client=Depends(get_mcp_client),
):
    """Останавливает лабу в рамках сессии."""
    try:
        ok = await stop_lab(db, session_id, current_user["id"], mcp_client)
    except MCPToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


@router.post("/{session_id}/restart")
async def restart_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    mcp_client=Depends(get_mcp_client),
):
    """Перезапускает лабу в рамках сессии."""
    try:
        ok = await restart_lab(db, session_id, current_user["id"], mcp_client)
    except MCPToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


@router.post("/{session_id}/reset")
async def reset_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
):
    """Сбрасывает лабу к исходному состоянию в рамках сессии."""
    if not await reset_lab(db, session_id, current_user["id"], gns3_client):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


@router.post("/{session_id}/end")
async def end_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
    monitor_registry: SessionMonitorRegistry = Depends(get_monitor_registry),
):
    """Завершает сессию и освобождает ресурсы GNS3."""
    if not await end_lab(db, session_id, current_user["id"], gns3_client, monitor_registry):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


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


@router.patch("/{session_id}", response_model=LearningSessionResponse)
async def update_session_endpoint(
    session_id: str,
    body: LearningSessionUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновляет статус сессии."""
    session = await end_session(db, session_id, current_user["id"], body.status)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return LearningSessionResponse(
        id=session.id,
        lab_slug=session.lab_slug,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        meta=session.meta,
    )


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
