"""Assignment and resolution of the experimental arm/group (merged from 4 modules).

Loop on/off axis: open (no proactivity) vs closed (closed loop).

Note (MRT, 2026-07): when `mrt_enabled` is set, the per-decision-point design is
primary (intervene/withhold randomization at the decision point, see
monitor._mrt_step). The per-session arm below is a coarse secondary contrast,
not the MRT trial's primary randomization.
"""
import random
from collections.abc import Callable
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class ControlArm(str, Enum):
    OPEN = "open"      # grounded reactive chat, proactivity suppressed
    CLOSED = "closed"  # closed loop


def assign_arm() -> ControlArm:
    """Random 50/50 arm assignment (coarse secondary contrast; MRT is per-decision-point)."""
    return random.choice([ControlArm.OPEN, ControlArm.CLOSED])


class ExperimentGroup(str, Enum):
    """Experiment groups."""

    GROUP_A = "group_a"
    GROUP_B = "group_b"


class AgentBackend(str, Enum):
    """Backend corresponding to the experiment group."""

    MULTI_AGENT = "multi_agent"
    OPENCLAW = "openclaw"


GROUP_TO_BACKEND = {
    ExperimentGroup.GROUP_A: AgentBackend.MULTI_AGENT,
    ExperimentGroup.GROUP_B: AgentBackend.OPENCLAW,
}


def assign_group() -> ExperimentGroup:
    """Random 50/50 group assignment."""
    return random.choice([ExperimentGroup.GROUP_A, ExperimentGroup.GROUP_B])


def parse_experiment_group(value: str | ExperimentGroup) -> ExperimentGroup:
    """String -> ExperimentGroup, for final letter groups only."""
    return value if isinstance(value, ExperimentGroup) else ExperimentGroup(value)


def backend_for_group(group: str | ExperimentGroup) -> AgentBackend:
    """Determine the backend from the experiment group."""
    return GROUP_TO_BACKEND[parse_experiment_group(group)]


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
    from models.lab import Lab
    from models.progress import LabProgress

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


async def assign_experiment_group_if_needed(
    db: AsyncSession,
    user_id: str,
    group_assigner: Callable[[], ExperimentGroup] = assign_group,
) -> None:
    """Assign an experiment group to the user, if not already assigned.

    group_assigner -- the group-selection function. Defaults to assign_group.
    Swapped for a deterministic lambda in tests.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is not None and user.experiment_group is None:
        user.experiment_group = group_assigner().value
