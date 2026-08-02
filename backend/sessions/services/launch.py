import logging

from sqlalchemy import func, select

from i18n import DEFAULT_LOCALE, Locale, LocalizedError
from labs.service import template_project_id_for
from models.lab import Lab
from models.session import LearningSession
from security.secrets import decrypt_secret, encrypt_secret
from sessions.services.proxy import existing_gns3_deep_url, existing_gns3_url
from sessions.services.query import get_active_session

logger = logging.getLogger(__name__)

MAX_CONCURRENT_SESSIONS_PER_USER = 2


async def count_active_sessions(db, user_id: str) -> int:
    """Counts the user's active and provisioning sessions."""
    result = await db.execute(
        select(func.count(LearningSession.id)).where(
            LearningSession.user_id == user_id,
            LearningSession.status.in_(("active", "provisioning")),
        )
    )
    return int(result.scalar_one() or 0)


async def _create_provisioning_row(db_factory, user_id: str, lab_slug: str, locale: Locale):
    """Creates a session row with status provisioning in a separate transaction."""
    async with db_factory() as db:
        session = LearningSession(
            user_id=user_id, lab_slug=lab_slug, status="provisioning", locale=locale
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session


async def _finalize_session_row(db_factory, session_id: str, status: str, meta: dict | None):
    """Updates the session's status and metadata after provisioning."""
    async with db_factory() as db:
        session = await db.get(LearningSession, session_id)
        session.status = status
        if meta is not None:
            session.meta = meta
        await db.commit()
        await db.refresh(session)
        return session


async def launch_session(
    db, user_id: str, lab_slug: str, gns3_client, db_factory, *, locale: Locale = DEFAULT_LOCALE
) -> tuple[LearningSession, dict]:
    """Launches a lab session.

    Returns the existing active session, or creates a new one via GNS3
    provisioning, checking the concurrent session limit and the presence
    of a lab template.
    """
    existing = await get_active_session(db, user_id, lab_slug)
    if existing:
        # Resume on a different locale than the one the session was launched with:
        # refresh it so background paths reading learning_sessions.locale stay current.
        if existing.locale != locale:
            existing.locale = locale
        meta = existing.meta or {}
        return existing, {
            "gns3_username": meta["gns3_username"],
            "gns3_password": decrypt_secret(meta["enc_password"]),
            "gns3_url": existing_gns3_url(existing),
            "gns3_deep_url": existing_gns3_deep_url(existing),
        }

    active_count = await count_active_sessions(db, user_id)
    if active_count >= MAX_CONCURRENT_SESSIONS_PER_USER:
        raise LocalizedError(
            "error.session.limit_reached", status_code=400, max=MAX_CONCURRENT_SESSIONS_PER_USER
        )

    lab = await db.get(Lab, lab_slug)
    if lab is None:
        raise LocalizedError("error.lab.not_found", status_code=400)

    if not lab.enabled:
        raise LocalizedError("error.lab.disabled", status_code=400)

    template_pid = template_project_id_for(lab)

    # Production split-tx scenario. Release the DB transaction during the gns3 call.
    session = await _create_provisioning_row(db_factory, user_id, lab_slug, locale)
    try:
        result = await gns3_client.create_session(user_id, template_pid)
    except Exception:
        await _finalize_session_row(db_factory, str(session.id), "error", None)
        logger.exception("GNS3 provisioning failed for session %s", session.id)
        raise

    meta = {
        "gns3_service_session_id": result["session_id"],
        "gns3_user_id": result["gns3_user_id"],
        "gns3_username": result["gns3_username"],
        "gns3_project_id": result["project_id"],
        "enc_password": encrypt_secret(result["gns3_password"]),
        "enc_jwt": encrypt_secret(result["gns3_jwt"]),
    }
    session = await _finalize_session_row(db_factory, str(session.id), "active", meta)

    return session, {
        "gns3_username": result["gns3_username"],
        "gns3_password": result["gns3_password"],
        "gns3_url": existing_gns3_url(session),
        "gns3_deep_url": existing_gns3_deep_url(session),
    }
