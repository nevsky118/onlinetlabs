from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab
from models.session import LearningSession


async def get_user_sessions(db: AsyncSession, user_id: str) -> list[LearningSession]:
    """Возвращает все сессии пользователя от новых к старым."""
    result = await db.execute(
        select(LearningSession)
        .where(LearningSession.user_id == user_id)
        .order_by(LearningSession.started_at.desc())
    )
    return list(result.scalars().all())


async def get_active_session(db, user_id: str, lab_slug: str):
    """Возвращает активную сессию пользователя по данной лабораторной, если есть."""
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.user_id == user_id,
            LearningSession.lab_slug == lab_slug,
            LearningSession.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def get_owned_session(db, session_id: str, user_id: str):
    """Возвращает сессию, проверяя что она принадлежит пользователю."""
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_session(db, session_id: str, user_id: str) -> LearningSession | None:
    """Возвращает сессию пользователя по идентификатору."""
    return await get_owned_session(db, session_id, user_id)


async def get_session_state(
    db, session_id: str, user_id: str, gns3_client, state_cache
) -> dict | None:
    """Возвращает обогащённое состояние сессии (с кэшем). None если сессия не найдена или чужая.

    Owner-check выполняется до похода в кэш, чтобы исключить cross-user попадания.
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
    raw = await gns3_client.get_state(gns3_sid)
    lab = await db.get(Lab, session.lab_slug)
    enriched = {
        "session_id": str(session.id),
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "lab": {"slug": session.lab_slug, "title": lab.title if lab else None},
        "nodes": raw.get("nodes", []),
        "links": raw.get("links", []),
        "metrics": raw.get("metrics", {}),
    }
    await state_cache.set(session_id, enriched)
    return enriched
