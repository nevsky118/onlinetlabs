"""Checking/recording/revoking consent. study covers everything; product is granular."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from control_interface.registry import ToolKind
from models.consent import Consent

# Bump when the wording changes; an older agreement then stops counting.
CURRENT_POLICY_VERSION = "1"

STUDY_SCOPE = "study"
PRODUCT_SCOPE = "product"
GRANTED = "granted"
DECLINED = "declined"


async def has_consent(db, user_id: str, kind: ToolKind) -> bool:
    """True when the learner has granted consent covering this tool kind."""
    rows = (
        (
            await db.execute(
                select(Consent).where(Consent.user_id == user_id, Consent.revoked_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    for c in rows:
        if c.decision != GRANTED:
            continue
        if c.scope == STUDY_SCOPE:
            return True
        if c.scope == PRODUCT_SCOPE:
            if kind == ToolKind.OBSERVE and c.observe:
                return True
            if kind == ToolKind.ACT and c.act:
                return True
    return False


async def study_decision(db, user_id: str) -> str | None:
    """The learner's answer for the current policy version, or None if never asked."""
    row = (
        await db.execute(
            select(Consent)
            .where(
                Consent.user_id == user_id,
                Consent.scope == STUDY_SCOPE,
                Consent.policy_version == CURRENT_POLICY_VERSION,
                Consent.revoked_at.is_(None),
            )
            .order_by(Consent.granted_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return row.decision if row else None


async def may_collect(db, user_id: str) -> bool:
    """True only on an explicit grant. Silence and refusal both mean no."""
    return await study_decision(db, user_id) == GRANTED


async def record(
    db,
    user_id: str,
    scope: str,
    observe: bool,
    act: bool,
    data_policy=None,
    decision: str = GRANTED,
    policy_version: str = CURRENT_POLICY_VERSION,
) -> Consent:
    """Writes the learner's answer. A refusal is stored, not an absence."""
    c = Consent(
        id=str(uuid4()),
        user_id=user_id,
        scope=scope,
        observe=observe and decision == GRANTED,
        act=act and decision == GRANTED,
        data_policy=data_policy,
        decision=decision,
        policy_version=policy_version,
    )
    db.add(c)
    await db.commit()
    return c


async def grant(
    db, user_id: str, scope: str, observe: bool, act: bool, data_policy=None
) -> Consent:
    """Records a grant."""
    return await record(db, user_id, scope, observe, act, data_policy, decision=GRANTED)


async def revoke(db, user_id: str, scope: str) -> int:
    """Marks the learner's active consents in this scope as revoked."""
    rows = (
        (
            await db.execute(
                select(Consent).where(
                    Consent.user_id == user_id, Consent.scope == scope, Consent.revoked_at.is_(None)
                )
            )
        )
        .scalars()
        .all()
    )
    now = datetime.now(UTC)
    for c in rows:
        c.revoked_at = now
    await db.commit()
    return len(rows)


async def list_active(db, user_id: str) -> list[Consent]:
    """Active (non-revoked) consents for the user."""
    result = await db.execute(
        select(Consent)
        .where(Consent.user_id == user_id, Consent.revoked_at.is_(None))
        .order_by(Consent.granted_at.desc())
    )
    return result.scalars().all()
