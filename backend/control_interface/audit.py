"""Append-only log of loop calls (observe/act). Dual-purpose: act = source of interventions."""

from datetime import UTC, datetime
from uuid import uuid4

from models.mcp_audit import MCPAudit


async def record(
    db, *, user_id, session_id, tool, kind, success, error=None, consent_ref=None, lab_slug=None
) -> None:
    db.add(
        MCPAudit(
            id=str(uuid4()),
            user_id=user_id,
            session_id=session_id,
            tool=tool,
            kind=kind,
            ts=datetime.now(UTC),
            success=success,
            error=error,
            consent_ref=consent_ref,
            lab_slug=lab_slug,
        )
    )
    await db.commit()
