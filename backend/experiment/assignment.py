"""Назначение и резолвинг экспериментального плеча/группы (собрано из 4 модулей).

Ось loop on/off: open (без проактива) vs closed (замкнутый контур).

Примечание (MRT, 2026-07): при `mrt_enabled` первичен per-decision-point дизайн
(рандомизация intervene/withhold в точке решения, см. monitor._mrt_step). Per-session
плечо ниже — грубый secondary contrast, не основная рандомизация MRT-испытания.
"""
import random
from collections.abc import Callable
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class ControlArm(str, Enum):
    OPEN = "open"      # заземлённый реактивный чат, проактив подавлен
    CLOSED = "closed"  # замкнутый контур


def assign_arm() -> ControlArm:
    """Случайное назначение плеча 50/50 (грубый secondary contrast; MRT — per-decision-point)."""
    return random.choice([ControlArm.OPEN, ControlArm.CLOSED])


class ExperimentGroup(str, Enum):
    """Группы эксперимента."""

    GROUP_A = "group_a"
    GROUP_B = "group_b"


class AgentBackend(str, Enum):
    """Бэкенд, соответствующий экспериментальной группе."""

    MULTI_AGENT = "multi_agent"
    OPENCLAW = "openclaw"


GROUP_TO_BACKEND = {
    ExperimentGroup.GROUP_A: AgentBackend.MULTI_AGENT,
    ExperimentGroup.GROUP_B: AgentBackend.OPENCLAW,
}


def assign_group() -> ExperimentGroup:
    """Случайное назначение группы 50/50."""
    return random.choice([ExperimentGroup.GROUP_A, ExperimentGroup.GROUP_B])


def parse_experiment_group(value: str | ExperimentGroup) -> ExperimentGroup:
    """Строка → ExperimentGroup, только для финальных буквенных групп."""
    return value if isinstance(value, ExperimentGroup) else ExperimentGroup(value)


def backend_for_group(group: str | ExperimentGroup) -> AgentBackend:
    """Определить бэкенд по группе эксперимента."""
    return GROUP_TO_BACKEND[parse_experiment_group(group)]


def skill_tag(lab) -> str | None:
    """Тег навыка лабы из meta['skill']. None, если не задан (near-transfer L2-проверка)."""
    return (getattr(lab, "meta", None) or {}).get("skill")


class UserNotFound(Exception):
    """Пользователь не найден при резолвинге плеча эксперимента."""

    pass


async def resolve_control_arm(db, user_id) -> ControlArm:
    """Читает User.control_arm; если не задано — назначает и персистит.

    Raises UserNotFound для несуществующего user_id (детерминированность: без
    персиста возврат случайного плеча плавал бы между вызовами).
    """
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise UserNotFound(f"User not found for experiment assignment: {user_id}")
    if not user.control_arm:
        user.control_arm = assign_arm().value
        await db.commit()
    return ControlArm(user.control_arm)


async def is_l2_session(db, user_id: str, lab_slug: str) -> bool:
    """True если пользователь уже завершил другую лабу того же навыка (L2-холдаут)."""
    from models.lab import Lab
    from models.progress import LabProgress

    current = (await db.execute(select(Lab).where(Lab.slug == lab_slug))).scalar_one_or_none()
    skill = skill_tag(current) if current else None
    if not skill:
        return False
    # slugи пройденных лаб того же навыка, кроме текущей
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
    """Эффективное плечо для сессии.

    На L2-холдауте (есть пройденная лаба того же навыка, но другая) →
    OPEN для ОБОИХ плеч; иначе базовое плечо.
    """
    if await is_l2_session(db, user_id, lab_slug):
        # L2-холдаут: проактив подавлен для всех
        return ControlArm.OPEN
    return await resolve_control_arm(db, user_id)


async def assign_experiment_group_if_needed(
    db: AsyncSession,
    user_id: str,
    group_assigner: Callable[[], ExperimentGroup] = assign_group,
) -> None:
    """Назначить экспериментальную группу пользователю, если ещё не назначена.

    group_assigner — функция выбора группы. Дефолт — assign_group.
    В тестах подменяется на детерминированную лямбду.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is not None and user.experiment_group is None:
        user.experiment_group = group_assigner().value
