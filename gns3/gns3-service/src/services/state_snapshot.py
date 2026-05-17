# Сбор актуального состояния сессии: список узлов, линков, агрегированные метрики.

from __future__ import annotations

import asyncio
import uuid as uuid_module
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Session, SessionStatus
from src.exceptions import SessionNotFound
from src.models import (
    LinkEndpoint,
    LinkState,
    NodeState,
    SessionMetrics,
    SessionStateResponse,
)

from .state_cache import StateCache

if TYPE_CHECKING:
    from src.gns3_admin_client import GNS3AdminClient


async def fetch_state(
    admin: GNS3AdminClient,
    cache: StateCache[SessionStateResponse],
    db: AsyncSession,
    session_id: str,
) -> SessionStateResponse:
    """Получить state-снапшот сессии с учётом TTL-кеша."""
    cached = cache.get(session_id)
    if cached is not None:
        return cached

    session = await db.get(Session, uuid_module.UUID(session_id))
    if session is None:
        raise SessionNotFound(f"Session {session_id} not found")

    project_id = session.gns3_project_id
    nodes_raw, links_raw = await asyncio.gather(
        admin.get_nodes(project_id),
        admin.get_links(project_id),
    )

    nodes = [
        NodeState(
            id=n["node_id"],
            name=n["name"],
            node_type=n["node_type"],
            status=n["status"],
            console=n.get("console"),
            console_type=n.get("console_type"),
            console_host=n.get("console_host", ""),
            symbol=n.get("symbol", ""),
        )
        for n in nodes_raw
    ]
    links = [
        LinkState(
            id=link["link_id"],
            nodes=[LinkEndpoint(**ep) for ep in link["nodes"]],
        )
        for link in links_raw
    ]
    nodes_started = sum(1 for n in nodes if n.status == "started")
    uptime = int((datetime.now(timezone.utc) - session.created_at).total_seconds())

    state = SessionStateResponse(
        session_id=str(session.id),
        project_id=project_id,
        status="active" if session.status == SessionStatus.ACTIVE else "closed",
        started_at=session.created_at,
        nodes=nodes,
        links=links,
        metrics=SessionMetrics(
            nodes_total=len(nodes),
            nodes_started=nodes_started,
            links_count=len(links),
            uptime_seconds=uptime,
        ),
    )
    cache.set(session_id, state)
    return state
