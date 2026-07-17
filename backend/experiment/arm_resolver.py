"""Перманентный резолвинг плеча эксперимента на пользователя."""

from sqlalchemy import select

from experiment.control_arm import ControlArm, assign_arm
from models.user import User


async def resolve_control_arm(db, user_id) -> ControlArm:
    """Читает User.control_arm; если не задано — назначает и персистит."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        return assign_arm()
    if not user.control_arm:
        user.control_arm = assign_arm().value
        await db.commit()
    return ControlArm(user.control_arm)


async def is_l2_session(db, user_id: str, lab_slug: str) -> bool:
    """True если пользователь уже завершил другую лабу того же навыка (L2-холдаут)."""
    from experiment.transfer import skill_tag
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
