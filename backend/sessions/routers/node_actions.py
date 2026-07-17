from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from deps import get_gns3_client, get_state_cache
from rate_limit import limiter
from sessions.service import proxy_bulk_node_action, proxy_node_action
from sessions.services.proxy import get_bulk_semaphore

router = APIRouter()

BackendNodeAction = Literal["start", "stop", "suspend", "reload"]


@router.post("/{session_id}/nodes/{node_id}/{action}")
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
    """Выполняет действие над узлом топологии (start, stop, suspend, reload)."""
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
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


@router.post("/{session_id}/nodes/{action}")
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
    """Выполняет действие сразу над всеми узлами топологии сессии."""
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
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}
