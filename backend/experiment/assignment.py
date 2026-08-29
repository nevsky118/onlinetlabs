"""Assignment and resolution of the control arm: open (no proactivity) vs closed.

Under mrt_enabled the primary randomization is per decision point, not per
session (see monitor._mrt_step); the arm is then a coarse secondary contrast.
"""

import random
from enum import Enum

from sqlalchemy import select

from models.catalog import Lab
from models.identity import User
from models.learning import LabProgress


class ControlArm(str, Enum):
    OPEN = "open"  # grounded reactive chat, proactivity suppressed
    CLOSED = "closed"  # closed loop


def assign_arm() -> ControlArm:
    """Random 50/50 arm assignment (coarse secondary contrast; MRT is per-decision-point)."""
    return random.choice([ControlArm.OPEN, ControlArm.CLOSED])


def skill_tag(lab) -> str | None:
    """Lab's skill tag from meta['skill']. None if not set (near-transfer L2 check)."""
    return (getattr(lab, "meta", None) or {}).get("skill")


class UserNotFound(Exception):
    """User not found while resolving the experiment arm."""

    pass


async def resolve_control_arm(db, user_id) -> ControlArm:
    """Reads User.control_arm; if unset, assigns and persists it.

    Raises UserNotFound for a nonexistent user_id (determinism: without
    persisting, a random arm would drift between calls).
    """
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise UserNotFound(f"User not found for experiment assignment: {user_id}")
    if not user.control_arm:
        user.control_arm = assign_arm().value
        await db.commit()
    return ControlArm(user.control_arm)


async def is_l2_session(db, user_id: str, lab_slug: str) -> bool:
    """True if the user has already completed another lab of the same skill (L2 holdout)."""

    current = (await db.execute(select(Lab).where(Lab.slug == lab_slug))).scalar_one_or_none()
    skill = skill_tag(current) if current else None
    if not skill:
        return False
    # slugs of completed labs with the same skill, excluding the current one
    completed_slugs = (
        (
            await db.execute(
                select(Lab.slug)
                .join(LabProgress, LabProgress.lab_slug == Lab.slug)
                .where(
                    LabProgress.user_id == user_id,
                    LabProgress.status == "completed",
                    Lab.slug != lab_slug,
                )
            )
        )
        .scalars()
        .all()
    )
    for prior_slug in completed_slugs:
        prior = (await db.execute(select(Lab).where(Lab.slug == prior_slug))).scalar_one_or_none()
        if prior and skill_tag(prior) == skill:
            return True
    return False


async def effective_arm(db, user_id: str, lab_slug: str) -> ControlArm:
    """Effective arm for a session.

    On an L2 holdout (a completed lab of the same skill exists, but a different
    one) -> OPEN for BOTH arms; otherwise the base arm.
    """
    if await is_l2_session(db, user_id, lab_slug):
        # L2 holdout: proactivity suppressed for everyone
        return ControlArm.OPEN
    return await resolve_control_arm(db, user_id)
