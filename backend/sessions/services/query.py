from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab
from models.session import LearningSession


async def get_user_sessions(db: AsyncSession, user_id: str) -> list[LearningSession]:
    """Returns all user sessions from newest to oldest."""
    result = await db.execute(
        select(LearningSession)
        .where(LearningSession.user_id == user_id)
        .order_by(LearningSession.started_at.desc())
    )
    return list(result.scalars().all())


async def get_active_session(db, user_id: str, lab_slug: str):
    """Returns the user's active session for the given lab, if any."""
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.user_id == user_id,
            LearningSession.lab_slug == lab_slug,
            LearningSession.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def get_owned_session(db, session_id: str, user_id: str):
    """Returns the session, verifying it belongs to the user."""
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_session(db, session_id: str, user_id: str) -> LearningSession | None:
    """Returns the user's session by identifier."""
    return await get_owned_session(db, session_id, user_id)


async def get_session_state(
    db, session_id: str, user_id: str, gns3_client, state_cache
) -> dict | None:
    """Returns the enriched session state (with caching). None if not found or not owned.

    The owner check runs before hitting the cache, to rule out cross-user hits.
    """
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return None
    cached = await state_cache.get(session_id)
    if cached is not None:
        return cached
    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if not gns3_sid:
        return None
    try:
        raw = await gns3_client.get_state(gns3_sid)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            # The GNS3 session disappeared (e.g. GNS3 infrastructure was restarted).
            # The platform session is orphaned; mark it ended so the user
            # doesn't get stuck and the next launch brings up a fresh environment.
            session.status = "ended"
            session.ended_at = datetime.now(UTC)
            await db.commit()
            return None
        raise
    lab = await db.get(Lab, session.lab_slug)
    from experiment.assignment import is_l2_session

    no_assist = await is_l2_session(db, user_id, session.lab_slug)
    enriched = {
        "session_id": str(session.id),
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "lab": {"slug": session.lab_slug, "title": lab.title if lab else None},
        "nodes": raw.get("nodes", []),
        "links": raw.get("links", []),
        "metrics": raw.get("metrics", {}),
        "no_assist": no_assist,
    }
    await state_cache.set(session_id, enriched)
    return enriched
