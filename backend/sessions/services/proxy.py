import asyncio

from fastapi import Request

from security.secrets import decrypt_secret
from sessions.services.query import get_owned_session


# Throttle для bulk-node-start. gns3-server одно-процессный async, насыщает
# docker.sock при >12 параллельных. На MSK-8 даёт пик CPU около 70 процентов.
_BULK_GNS3_SEMAPHORE = asyncio.Semaphore(12)


def get_bulk_semaphore(request: Request) -> asyncio.Semaphore:
    """DI: вернёт семафор из app.state, либо модульный фоллбек.

    Тесты подменяют app.state.bulk_gns3_semaphore, чтобы не блокировать
    параллельные сценарии лимитом продового семафора.
    """
    return getattr(request.app.state, "bulk_gns3_semaphore", _BULK_GNS3_SEMAPHORE)


def existing_gns3_url(session) -> str:
    """Возвращает публичный URL GNS3."""
    from config import settings
    return settings.gns3.public_url


def existing_gns3_deep_url(session) -> str:
    """Возвращает глубокую ссылку на проект сессии в веб-интерфейсе GNS3."""
    from config import settings
    project_id = (session.meta or {}).get("gns3_project_id")
    if not project_id:
        return settings.gns3.public_url
    return f"{settings.gns3.public_url.rstrip('/')}/static/web-ui/controller/1/project/{project_id}"


async def get_credentials(db, session_id: str, user_id: str) -> dict | None:
    """Возвращает доступы и ссылки GNS3 для сессии. None если сессия чужая или без метаданных."""
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
    db, session_id: str, user_id: str, node_id: str, action: str,
    gns3_client, state_cache,
) -> bool:
    """Выполняет действие над узлом в GNS3 и сбрасывает кэш состояния. False если сессия чужая."""
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
    db, session_id: str, user_id: str, action: str,
    gns3_client, state_cache,
    semaphore: asyncio.Semaphore | None = None,
) -> bool:
    """Выполняет массовое действие над узлами в GNS3 под семафором. False если сессия чужая."""
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
    db, session_id: str, user_id: str, limit: int, cursor: str | None,
    gns3_client,
) -> dict | None:
    """Возвращает ленту активности сессии из GNS3. None если сессия чужая."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return None
    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if not gns3_sid:
        return None
    return await gns3_client.get_activity(gns3_sid, limit=limit, cursor=cursor)
