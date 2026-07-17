"""Эндпоинты запуска сессии и статуса очереди."""

import logging

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request as FastAPIRequest
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_active_user
from db.session import get_db, get_db_factory
from deps import get_gns3_client, get_monitor_registry
from rate_limit import limiter
from sessions.context import build_session_context
from sessions.monitor_registry import SessionMonitorRegistry
from sessions.queue import QUEUE_AVG_PROVISION_SEC, SessionQueueService, get_queue_service
from sessions.schemas import LaunchResponse, LearningSessionCreate
from sessions.service import get_active_session, launch_session

logger = logging.getLogger(__name__)

router = APIRouter()


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
):
    """Запускает лабу и создаёт сессию с выдачей доступов к GNS3.

    Если свободных слотов нет, ставит пользователя в очередь и возвращает её позицию.
    """
    # Прокидываем user_id и lab_slug в structlog contextvars, чтобы все
    # последующие логи в рамках запроса автоматически содержали эти поля.
    structlog.contextvars.bind_contextvars(user_id=current_user["id"], lab_slug=body.lab_slug)
    # Релонч уже активной сессии не должен брать слот очереди и задваивать
    # счётчики: слот/мониторинг/gauge трогаем только для нового запуска.
    existing = await get_active_session(db, current_user["id"], body.lab_slug)
    is_new_launch = existing is None

    if is_new_launch:
        acquired = await queue.try_acquire(current_user["id"], body.lab_slug)
        if not acquired:
            pos = await queue.enqueue(current_user["id"], body.lab_slug)
            depth = await queue.queue_depth(body.lab_slug)
            eta_sec = depth * QUEUE_AVG_PROVISION_SEC
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
        if is_new_launch:
            await queue.release(body.lab_slug)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        if is_new_launch:
            await queue.release(body.lab_slug)
        raise HTTPException(status_code=502, detail="GNS3 provisioning failed")
    structlog.contextvars.bind_contextvars(session_id=session.id)
    if is_new_launch and session.status == "active":
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
        "eta_sec": pos * QUEUE_AVG_PROVISION_SEC,
    }
