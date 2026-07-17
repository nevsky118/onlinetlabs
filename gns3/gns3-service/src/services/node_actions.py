# Operations on nodes of a session's project: single and bulk.

from __future__ import annotations

import uuid as uuid_module
from typing import TYPE_CHECKING

from src.db.models import Session, SessionStatus
from src.exceptions import SessionClosed, SessionNotFound

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.clients.admin import GNS3AdminClient


async def _load_active_session(db: AsyncSession, session_id: str) -> Session:
    session = await db.get(Session, uuid_module.UUID(session_id))
    if session is None:
        raise SessionNotFound(f"Session {session_id} not found")
    if session.status != SessionStatus.ACTIVE:
        raise SessionClosed(f"Session {session_id} is closed")
    return session


async def run_node_action(
    admin: GNS3AdminClient,
    db: AsyncSession,
    session_id: str,
    node_id: str,
    action: str,
) -> None:
    """Run an action on a single session node."""
    session = await _load_active_session(db, session_id)
    await admin.node_action(session.gns3_project_id, node_id, action)


async def run_bulk_node_action(
    admin: GNS3AdminClient,
    db: AsyncSession,
    session_id: str,
    action: str,
) -> None:
    """Apply an action to all nodes of the session's project at once."""
    session = await _load_active_session(db, session_id)
    await admin.bulk_node_action(session.gns3_project_id, action)
