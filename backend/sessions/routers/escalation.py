"""Endpoint for the "need a mentor" button."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from i18n import LocalizedError
from kit.db import get_db
from sessions.activity import touch_path_session
from sessions.service import get_session
from sessions.services.escalation import record_escalation

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users/me/sessions",
    tags=["escalation"],
    dependencies=[Depends(touch_path_session)],
)


@router.post("/{session_id}/escalate", status_code=204)
async def escalate_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manual escalation via the "need a mentor" button."""
    session = await get_session(db, session_id, current_user["id"])
    if session is None:
        raise LocalizedError("error.session.not_found", status_code=404)
    await record_escalation(db, session_id, current_user["id"], session.lab_slug, source="manual")
