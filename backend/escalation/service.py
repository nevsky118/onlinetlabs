"""Escalation = a request for a mentor. Arm-neutral: button or objective."""

from datetime import UTC, datetime
from uuid import uuid4

from models.behavioral_event import BehavioralEvent


async def record_escalation(db, session_id, user_id, lab_slug, source: str) -> None:
    """Record an escalation event (source: 'manual' | 'objective')."""
    now = datetime.now(tz=UTC)
    db.add(
        BehavioralEvent(
            id=str(uuid4()),
            session_id=session_id,
            user_id=user_id,
            lab_slug=lab_slug,
            timestamp=now,
            event_type="escalation",
            action=source,
            success=False,
            severity="warn",
            message="нужен наставник",
            created_at=now,
        )
    )
    await db.commit()
