import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab
from models.session import LearningSession
from sessions.context import build_session_context
from sessions.services.query import get_owned_session

logger = logging.getLogger(__name__)


async def end_session(
    db: AsyncSession, session_id: str, user_id: str, status: str
) -> LearningSession | None:
    """Завершает сессию пользователя, проставляя статус и время окончания."""
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None
    session.status = status
    session.ended_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


async def stop_lab(db, session_id: str, user_id: str, mcp_client) -> bool:
    """Останавливает все узлы лабораторной через MCP. False если сессия чужая."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    ctx = build_session_context(session)
    await mcp_client.execute_action(ctx, "stop_all_nodes", {})
    return True


async def restart_lab(db, session_id: str, user_id: str, mcp_client) -> bool:
    """Перезапускает узлы лабораторной через MCP. False если сессия чужая."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    ctx = build_session_context(session)
    await mcp_client.execute_action(ctx, "stop_all_nodes", {})
    await mcp_client.execute_action(ctx, "start_all_nodes", {})
    return True


async def reset_lab(db, session_id: str, user_id: str, gns3_client) -> bool:
    """Пересоздаёт проект GNS3 из шаблона и обновляет id проекта в сессии."""
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    lab = await db.get(Lab, session.lab_slug)
    if session.lab_slug.endswith("-ccna"):
        template_pid = lab.gns3_template_project_id_iosvl2
    else:
        template_pid = lab.gns3_template_project_id
    meta = dict(session.meta or {})
    result = await gns3_client.reset_project(meta["gns3_service_session_id"], template_pid)
    meta["gns3_project_id"] = result["project_id"]
    session.meta = meta  # reassign so SQLAlchemy detects JSON change
    await db.commit()
    return True


async def end_lab(db, session_id: str, user_id: str, gns3_client, monitor_registry) -> bool:
    """Завершает лабораторную.

    Удаляет сессию gns3-service, останавливает монитор, помечает сессию ended,
    освобождает место в очереди и уменьшает счётчик активных сессий.
    """
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        return False
    meta = session.meta or {}
    if meta.get("gns3_service_session_id"):
        try:
            await gns3_client.delete_session(meta["gns3_service_session_id"])
        except Exception:
            logger.exception("Teardown gns3-service упал для %s", session_id)
    await monitor_registry.stop(session_id)
    lab_slug = session.lab_slug
    session.status = "ended"
    session.ended_at = datetime.now(timezone.utc)
    await db.commit()
    from sessions.queue import _get_or_create_singleton
    queue = _get_or_create_singleton()
    await queue.release(lab_slug)
    try:
        from observability.metrics import active_sessions_gauge
        active_sessions_gauge.labels(lab_slug=lab_slug).dec()
    except Exception:
        pass  # metrics optional
    return True
