"""Session liveness stamps: request activity and observed device changes."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Request
from sqlalchemy import update

from auth.dependencies import get_current_user
from kit.db import get_db
from models.learning import LearningSession

logger = logging.getLogger(__name__)

TOUCH_THROTTLE_SEC = 30

_PATH_PARAMS = ("session_id", "sid")


async def touch_session(db, session_id: str, user_id: str) -> None:
    """Stamps last_seen_at, at most once per throttle window, owner-scoped.

    Never raises: liveness is bookkeeping and must not be able to fail a request
    or drop a websocket.
    """
    now = datetime.now(UTC)
    try:
        await db.execute(
            update(LearningSession)
            .where(
                LearningSession.id == session_id,
                LearningSession.user_id == user_id,
                LearningSession.last_seen_at < now - timedelta(seconds=TOUCH_THROTTLE_SEC),
            )
            .values(last_seen_at=now)
        )
        await db.commit()
    except Exception:
        logger.warning("touch_session failed for %s", session_id, exc_info=True)


async def touch_path_session(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> None:
    """Router-level dependency: stamps whichever session the path names."""
    session_id = next(
        (request.path_params[p] for p in _PATH_PARAMS if p in request.path_params), None
    )
    if not session_id:
        return
    await touch_session(db, str(session_id), current_user["id"])


async def touch_observed_session(db_factory, session_id: str) -> None:
    """Stamps a session whose device state changed: the console-work signal."""
    now = datetime.now(UTC)
    try:
        async with db_factory() as db:
            await db.execute(
                update(LearningSession)
                .where(
                    LearningSession.id == session_id,
                    LearningSession.last_seen_at < now - timedelta(seconds=TOUCH_THROTTLE_SEC),
                )
                .values(last_seen_at=now)
            )
            await db.commit()
    except Exception:
        logger.warning("touch_observed_session failed for %s", session_id, exc_info=True)
