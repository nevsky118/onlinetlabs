# Операции над узлами проекта сессии: одиночные и bulk.

from __future__ import annotations

import uuid as uuid_module
from typing import TYPE_CHECKING

from src.db.models import Session, SessionStatus
from src.exceptions import SessionClosed, SessionNotFound

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.gns3_admin_client import GNS3AdminClient


async def _load_active_session(db: "AsyncSession", session_id: str) -> Session:
    session = await db.get(Session, uuid_module.UUID(session_id))
    if session is None:
        raise SessionNotFound(f"Session {session_id} not found")
    if session.status != SessionStatus.ACTIVE:
        raise SessionClosed(f"Session {session_id} is closed")
    return session


async def run_node_action(
    admin: "GNS3AdminClient",
    db: "AsyncSession",
    session_id: str,
    node_id: str,
    action: str,
) -> None:
    """Запустить действие над одним узлом сессии."""
    session = await _load_active_session(db, session_id)
    await admin.node_action(session.gns3_project_id, node_id, action)


async def run_bulk_node_action(
    admin: "GNS3AdminClient",
    db: "AsyncSession",
    session_id: str,
    action: str,
) -> None:
    """Применить действие сразу ко всем узлам проекта сессии."""
    session = await _load_active_session(db, session_id)
    await admin.bulk_node_action(session.gns3_project_id, action)
