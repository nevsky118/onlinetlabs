import asyncio
from urllib.parse import urlencode

from fastapi import Request

from security.secrets import decrypt_secret
from sessions.services.query import get_owned_session

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


def existing_gns3_deep_url(session) -> str:
    """Returns a deep link to the session's project in the GNS3 web UI.

    Goes through auth-relay.html (see gns3/gns3-server/auth-relay.html): a
    direct jump to /controller/1/project/<id> hits the GNS3 login form;
    the relay fills it with the temporary gns3_username/gns3_password and
    gets the student to the project's returnUrl with a single "Log in" click.
    """
    from config import settings

    meta = session.meta or {}
    project_id = meta.get("gns3_project_id")
    base = settings.gns3.public_url.rstrip("/")
    if not project_id:
        return settings.gns3.public_url
    username = meta.get("gns3_username")
    enc_password = meta.get("enc_password")
    if username and enc_password:
        query = urlencode(
            {
                "username": username,
                "password": decrypt_secret(enc_password),
                "project": project_id,
            }
        )
        return f"{base}/static/web-ui/auth-relay.html?{query}"
    return f"{base}/static/web-ui/controller/1/project/{project_id}"


async def get_credentials(db, session_id: str, user_id: str) -> dict | None:
    """Returns GNS3 credentials and links for the session. None if not owned or no metadata."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None or not session.meta:
        return None
    meta = session.meta
    return {
        "gns3_username": meta["gns3_username"],
        "gns3_password": decrypt_secret(meta["enc_password"]),
        "gns3_url": existing_gns3_url(session),
        "gns3_deep_url": existing_gns3_deep_url(session),
    }


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
    await gns3_client.node_action(gns3_sid, node_id, action)
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
    sem = semaphore if semaphore is not None else _BULK_GNS3_SEMAPHORE
    async with sem:
        await gns3_client.bulk_node_action(gns3_sid, action)
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
