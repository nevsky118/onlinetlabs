"""Account preferences and login sessions, owner-scoped."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from i18n import LocalizedError
from models.identity import Session, User


async def get_preferences(db: AsyncSession, user_id: str) -> User:
    """The caller's user row, or a localized 404."""
    user = await db.get(User, user_id)
    if user is None:
        raise LocalizedError("error.user.not_found", status_code=404)
    return user


async def set_default_model(
    db: AsyncSession, user_id: str, model_id: str | None, *, can_select: bool
) -> User:
    """Sets or clears the preferred model. Clearing needs no entitlement."""
    user = await get_preferences(db, user_id)
    if model_id is not None:
        if not can_select:
            raise LocalizedError("error.user.model_selection_denied", status_code=403)
        if settings.agents.get_entry(model_id) is None:
            raise LocalizedError("error.user.unknown_model", status_code=422)
    user.default_model_id = model_id
    await db.commit()
    await db.refresh(user)
    return user


async def list_login_sessions(db: AsyncSession, user_id: str) -> list[Session]:
    """The caller's login sessions, longest-lived first."""
    result = await db.execute(
        select(Session).where(Session.user_id == user_id).order_by(Session.expires.desc())
    )
    return list(result.scalars().all())


async def revoke_login_session(db: AsyncSession, user_id: str, session_id: str) -> int:
    """Revokes one of the caller's login sessions."""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise LocalizedError("error.session.not_found", status_code=404)
    await db.delete(session)
    await db.commit()
    return 1


async def revoke_all_login_sessions(db: AsyncSession, user_id: str) -> int:
    """Revokes every login session the caller holds."""
    result = await db.execute(delete(Session).where(Session.user_id == user_id))
    await db.commit()
    return result.rowcount
