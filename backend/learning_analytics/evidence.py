"""D4: запись сырых evidence-снимков для слепой разметки (disjoint от признаков)."""
import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from models.session_evidence_snapshot import SessionEvidenceSnapshot


async def capture_snapshot(
    db: AsyncSession, session_id: str, user_id: str, lab_slug: str,
    kind: str, payload: dict,
) -> None:
    """Записать сырой evidence-снимок.

    payload приводится к JSON-safe (`default=str` покрывает datetime и пр.),
    чтобы произвольные MCP-наблюдения сериализовались без падения.
    """
    safe = json.loads(json.dumps(payload, default=str))
    db.add(SessionEvidenceSnapshot(
        id=str(uuid4()), session_id=session_id, user_id=user_id, lab_slug=lab_slug,
        ts=datetime.now(tz=UTC), kind=kind, payload=safe,
    ))
    await db.commit()
