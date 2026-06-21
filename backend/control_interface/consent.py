"""Проверка/выдача/отзыв согласия. study покрывает всё; product гранулярно."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from control_interface.registry import ToolKind
from models.consent import Consent


async def has_consent(db, user_id: str, kind: ToolKind) -> bool:
    rows = (await db.execute(
        select(Consent).where(Consent.user_id == user_id, Consent.revoked_at.is_(None))
    )).scalars().all()
    for c in rows:
        if c.scope == "study":
            return True  # участие в эксперименте покрывает observe+act
        if c.scope == "product":
            if kind == ToolKind.OBSERVE and c.observe:
                return True
            if kind == ToolKind.ACT and c.act:
                return True
    return False


async def grant(db, user_id: str, scope: str, observe: bool, act: bool, data_policy=None) -> Consent:
    c = Consent(id=str(uuid4()), user_id=user_id, scope=scope, observe=observe, act=act, data_policy=data_policy)
    db.add(c)
    await db.commit()
    return c


async def revoke(db, user_id: str, scope: str) -> int:
    rows = (await db.execute(
        select(Consent).where(Consent.user_id == user_id, Consent.scope == scope, Consent.revoked_at.is_(None))
    )).scalars().all()
    now = datetime.now(timezone.utc)
    for c in rows:
        c.revoked_at = now
    await db.commit()
    return len(rows)
