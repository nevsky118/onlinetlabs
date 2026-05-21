"""Эндпоинты управления сессией: stop, restart, reset, end, patch."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from deps import get_gns3_client, get_mcp_client, get_monitor_registry
from mcp_client.client import MCPToolError
from sessions.monitor_registry import SessionMonitorRegistry
from sessions.schemas import LearningSessionResponse, LearningSessionUpdate
from sessions.service import end_lab, end_session, reset_lab, restart_lab, stop_lab

logger = logging.getLogger(__name__)

router = APIRouter()


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
