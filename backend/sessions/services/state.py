"""The enriched, cached view of a live session."""

import httpx

from experiment.assignment import is_l2_session
from i18n import DEFAULT_LOCALE, Locale, resolve_localized
from models.catalog import Lab
from sessions.services.lifecycle import _mark_ended_and_finalize
from sessions.services.query import get_owned_session


async def get_session_state(
    db, session_id: str, user_id: str, gns3_client, state_cache, locale: Locale = DEFAULT_LOCALE
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
            # The platform session is orphaned; finalize it so the user doesn't get
            # stuck, the next launch brings up a fresh environment and the slot frees.

            await _mark_ended_and_finalize(db, session, status="ended")
            return None
        raise
    lab = await db.get(Lab, session.lab_slug)

    no_assist = await is_l2_session(db, user_id, session.lab_slug)
    enriched = {
        "session_id": str(session.id),
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "lab": {
            "slug": session.lab_slug,
            "title": resolve_localized(lab.title_i18n, locale) if lab else None,
        },
        "nodes": raw.get("nodes", []),
        "links": raw.get("links", []),
        "metrics": raw.get("metrics", {}),
        "no_assist": no_assist,
        "paused": session.paused_at is not None,
    }
    await state_cache.set(session_id, enriched)
    return enriched
