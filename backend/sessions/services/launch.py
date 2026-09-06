import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from config import settings
from i18n import DEFAULT_LOCALE, Locale, LocalizedError
from kit.secrets import encrypt_secret
from labs.service import template_project_id_for
from models.catalog import Lab
from models.learning import LearningSession
from sessions.services.proxy import session_credentials as _credentials
from sessions.services.query import get_active_session
from sessions.services.ticket import TicketStore, get_ticket_store

logger = logging.getLogger(__name__)

# kept as a module attribute: sessions.service re-exports it
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


async def _enforce_user_cap(db, user_id: str) -> None:
    """Serialises this learner's launches, then rechecks the per-user limit.

    The caller's own check is a count followed by an insert, and two launches on
    different labs would both pass it: the partial unique index only stops twins of
    the same lab. The advisory lock is held to the end of this transaction, so the
    recount below sees every row a concurrent launch has committed.

    Postgres only. Bound to anything else, or to one of the doubles the unit suite
    passes in, this is skipped: the caller's check still applies, and the databases
    that skip it serialise writers anyway.
    """
    bind = getattr(db, "bind", None)
    if bind is None or bind.dialect.name != "postgresql":
        return

    await db.execute(select(func.pg_advisory_xact_lock(func.hashtext(user_id))))
    max_per_user = settings.capacity.max_sessions_per_user
    if await count_active_sessions(db, user_id) >= max_per_user:
        raise LocalizedError("error.session.limit_reached", status_code=400, max=max_per_user)


async def _create_provisioning_row(db_factory, user_id: str, lab_slug: str, locale: Locale):
    """Creates a session row with status provisioning in a separate transaction.

    A partial unique index allows one live session per learner and lab, so a
    second concurrent launch loses the race here rather than creating a twin.
    """
    async with db_factory() as db:
        await _enforce_user_cap(db, user_id)
        session = LearningSession(
            user_id=user_id,
            lab_slug=lab_slug,
            status="provisioning",
            locale=locale,
            expires_at=datetime.now(UTC) + timedelta(hours=settings.capacity.session_max_hours),
        )
        db.add(session)
        try:
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            raise LocalizedError("error.session.already_launching", status_code=409) from exc
        await db.refresh(session)
        return session


async def _finalize_session_row(db_factory, session_id: str, status: str, meta: dict | None):
    """Updates the session's status and metadata after provisioning.

    Returns None if the row is already gone: the reaper and an admin erasure can both
    delete it while GNS3 is still provisioning. The caller is finishing a session that
    no longer exists either way, and on the failure path an AttributeError here would
    replace the provisioning error the caller is about to re-raise.
    """
    async with db_factory() as db:
        session = await db.get(LearningSession, session_id)
        if session is None:
            logger.warning("session row %s disappeared before finalization", session_id)
            return None
        session.status = status
        if meta is not None:
            session.meta = meta
        await db.commit()
        await db.refresh(session)
        return session


async def launch_session(
    db,
    user_id: str,
    lab_slug: str,
    gns3_client,
    db_factory,
    *,
    locale: Locale = DEFAULT_LOCALE,
    ticket_store: TicketStore | None = None,
) -> tuple[LearningSession, dict, bool]:
    """Launches a lab session.

    Returns the existing active session, or creates a new one via GNS3
    provisioning, checking the concurrent session limit and the presence
    of a lab template.

    The third element says whether this call created the session. The caller decides
    on it whether to keep the queue slot it took, start a monitor and count the
    session, and it cannot infer that from its own earlier lookup: a launch that
    raced ours may have made the session active in between.

    ticket_store is injected like gns3_client and db_factory; it defaults to the
    process-wide store backed by redis.
    """
    tickets = ticket_store or get_ticket_store()
    existing = await get_active_session(db, user_id, lab_slug)
    if existing:
        # Resume on a different locale than the one the session was launched with:
        # refresh it so background paths reading learning_sessions.locale stay current.
        if existing.locale != locale:
            existing.locale = locale
        ticket = await tickets.issue(str(existing.id), user_id)
        return existing, _credentials(existing, ticket), False

    max_per_user = settings.capacity.max_sessions_per_user
    active_count = await count_active_sessions(db, user_id)
    if active_count >= max_per_user:
        raise LocalizedError("error.session.limit_reached", status_code=400, max=max_per_user)

    lab = await db.get(Lab, lab_slug)
    if lab is None:
        raise LocalizedError("error.lab.not_found", status_code=400)

    if not lab.enabled:
        raise LocalizedError("error.lab.disabled", status_code=400)

    template_pid = template_project_id_for(lab)

    # Production split-tx scenario. Release the DB transaction during the gns3 call.
    provisioning = await _create_provisioning_row(db_factory, user_id, lab_slug, locale)
    try:
        result = await gns3_client.create_session(user_id, template_pid)
    except Exception:
        await _finalize_session_row(db_factory, str(provisioning.id), "error", None)
        logger.exception("GNS3 provisioning failed for session %s", provisioning.id)
        raise

    meta = {
        "gns3_service_session_id": result["session_id"],
        "gns3_user_id": result["gns3_user_id"],
        "gns3_username": result["gns3_username"],
        "gns3_project_id": result["project_id"],
        "enc_password": encrypt_secret(result["gns3_password"]),
        "enc_jwt": encrypt_secret(result["gns3_jwt"]),
    }
    session = await _finalize_session_row(db_factory, str(provisioning.id), "active", meta)
    if session is None:
        raise LocalizedError("error.session.not_found", status_code=409)

    # Only the built-in switch comes up on its own; the hosts a student is asked to
    # configure would otherwise land stopped. Not fatal: the session is usable and
    # the start control stays in the UI.
    try:
        await gns3_client.bulk_node_action(result["session_id"], "start")
    except Exception:
        logger.exception("could not start nodes for session %s", session.id)

    ticket = await tickets.issue(str(session.id), user_id)
    return session, _credentials(session, ticket), True
