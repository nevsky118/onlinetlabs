"""Эскалация = спрос на наставника. Arm-нейтрально: кнопка или объективно."""
from datetime import datetime, timezone
from uuid import uuid4

from models.behavioral_event import BehavioralEvent


async def record_escalation(db, session_id, user_id, lab_slug, source: str) -> None:
    """Записать событие эскалации (source: 'manual' | 'objective')."""
    now = datetime.now(tz=timezone.utc)
    db.add(BehavioralEvent(
        id=str(uuid4()), session_id=session_id, user_id=user_id, lab_slug=lab_slug,
        timestamp=now, event_type="escalation", action=source, success=False,
        severity="warn", message="нужен наставник", created_at=now,
    ))
    await db.commit()
