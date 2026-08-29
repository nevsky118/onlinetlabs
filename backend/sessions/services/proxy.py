import asyncio
from urllib.parse import urlencode

from fastapi import Request

from config import settings
from security.secrets import decrypt_secret
from sessions.services.persist import persist_volatile_configs
from sessions.services.query import get_owned_session
from sessions.services.ticket import get_ticket_store

# Throttle for bulk-node-start. gns3-server is single-process async and
# saturates docker.sock above 12 parallel calls. On MSK-8 this peaks CPU at about 70 percent.
_BULK_GNS3_SEMAPHORE = asyncio.Semaphore(12)


def get_bulk_semaphore(request: Request) -> asyncio.Semaphore:
    """Returns the semaphore from app.state, or the module-level fallback, for dependency injection.

    Tests override app.state.bulk_gns3_semaphore so parallel test scenarios
    aren't blocked by the production semaphore's limit.
    """
    return getattr(request.app.state, "bulk_gns3_semaphore", _BULK_GNS3_SEMAPHORE)


def existing_gns3_url(session) -> str:
    """Returns the public GNS3 URL."""
    from config import settings

    return settings.gns3.public_url


def existing_gns3_deep_url(session, ticket: str | None = None) -> str:
    """Returns a deep link to the session's project in the GNS3 web UI.

    Goes through auth-relay.html: a direct jump to /controller/1/project/<id>
    hits the GNS3 login form. The relay exchanges a one-time ticket for a JWT
    server-side, so no password reaches the browser.
    """
    from config import settings

    meta = session.meta or {}
    project_id = meta.get("gns3_project_id")
    base = settings.gns3.public_url.rstrip("/")
    if not project_id:
        return settings.gns3.public_url
    if ticket:
        query = urlencode({"ticket": ticket, "project": project_id})
        return f"{base}/static/web-ui/auth-relay.html?{query}"
    return f"{base}/static/web-ui/controller/1/project/{project_id}"


async def get_credentials(db, session_id: str, user_id: str) -> dict | None:
    """Returns the GNS3 links for the session. None if not owned or no metadata."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None or not session.meta:
        return None
    meta = session.meta
    ticket = await get_ticket_store().issue(str(session.id), user_id)
    return {
        "gns3_username": meta["gns3_username"],
        "gns3_url": existing_gns3_url(session),
        "gns3_deep_url": existing_gns3_deep_url(session, ticket),
    }


async def redeem_gns3_ticket(db, ticket: str, gns3_client) -> dict | None:
    """Exchanges a one-time ticket for a fresh GNS3 JWT and the project to open."""
    payload = await get_ticket_store().redeem(ticket)
    if payload is None:
        return None
    session = await get_owned_session(db, payload["session_id"], payload["user_id"])
    if session is None or not session.meta:
        return None
    meta = session.meta
    gns3_sid = meta.get("gns3_service_session_id")
    if not gns3_sid:
        return None
    jwt = await gns3_client.issue_session_token(gns3_sid, decrypt_secret(meta["enc_password"]))
    return {
        "gns3_jwt": jwt,
        "project_id": meta.get("gns3_project_id"),
        "gns3_url": existing_gns3_url(session),
    }


async def _clear_paused(db, session) -> None:
    """Resume: a started node means the session is no longer paused."""
    if session.paused_at is None:
        return
    session.paused_at = None
    await db.commit()


async def proxy_node_action(
    db,
    session_id: str,
    user_id: str,
    node_id: str,
    action: str,
    gns3_client,
    state_cache,
) -> bool:
    """Performs an action on a node in GNS3 and invalidates the state cache. False if not owned."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if not gns3_sid:
        return False
    if action == "stop":
        await persist_volatile_configs(gns3_client, gns3_sid, settings)
    await gns3_client.node_action(gns3_sid, node_id, action)
    if action == "start":
        await _clear_paused(db, session)
    await state_cache.invalidate(session_id)
    return True


async def proxy_bulk_node_action(
    db,
    session_id: str,
    user_id: str,
    action: str,
    gns3_client,
    state_cache,
    semaphore: asyncio.Semaphore | None = None,
) -> bool:
    """Performs a bulk action on nodes in GNS3 under a semaphore. False if not owned."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if not gns3_sid:
        return False
    if action == "stop":
        await persist_volatile_configs(gns3_client, gns3_sid, settings)
    sem = semaphore if semaphore is not None else _BULK_GNS3_SEMAPHORE
    async with sem:
        await gns3_client.bulk_node_action(gns3_sid, action)
    if action == "start":
        await _clear_paused(db, session)
    await state_cache.invalidate(session_id)
    return True


async def proxy_activity(
    db,
    session_id: str,
    user_id: str,
    limit: int,
    cursor: str | None,
    gns3_client,
) -> dict | None:
    """Returns the session's activity feed from GNS3. None if not owned."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return None
    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if not gns3_sid:
        return None
    return await gns3_client.get_activity(gns3_sid, limit=limit, cursor=cursor)
