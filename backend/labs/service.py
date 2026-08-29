import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from i18n import LocalizedError, as_locale_map
from kit.db import async_session
from labs.readiness import (
    NO_TEMPLATE_FRR,
    NO_TEMPLATE_IOSVL2,
    audit_labs,
    resolve_template_id,
)
from models.catalog import Lab
from validation.runner import spec_slugs

logger = logging.getLogger(__name__)


async def get_all_labs(
    db: AsyncSession, course_slug: str | None = None, *, enabled_only: bool = False
) -> list[Lab]:
    """Selects labs from the DB, optionally filtered by course, ordered by sort order.

    `enabled_only` is opt-in: admin listings must keep seeing disabled labs.
    """
    stmt = select(Lab)
    if course_slug is not None:
        stmt = stmt.where(Lab.course_slug == course_slug)
    if enabled_only:
        stmt = stmt.where(Lab.enabled.is_(True))
    stmt = stmt.order_by(Lab.order_in_course)
    result = await db.execute(stmt)
    return list(result.scalars().all())


def template_project_id_for(lab: Lab) -> str:
    """GNS3 template project id for the lab, chosen by slug suffix.

    Single source for launch and reset; they used to branch differently.
    """
    template_pid, blocker = resolve_template_id(lab)
    if template_pid:
        return template_pid
    if blocker == NO_TEMPLATE_IOSVL2:
        raise LocalizedError("error.lab.iosvl2_missing", status_code=400, slug=lab.slug)
    if blocker == NO_TEMPLATE_FRR:
        raise LocalizedError("error.lab.no_template", status_code=400)
    raise LocalizedError("error.lab.no_template_project", status_code=400)


async def create_lab(
    db: AsyncSession,
    slug: str,
    title: str | dict,
    description: str | dict | None = None,
    difficulty: str = "beginner",
    environment_type: str = "none",
    gns3_template_project_id: str | None = None,
) -> Lab:
    """Creates and saves a new lab. A bare string title is stored under the default locale."""
    lab = Lab(
        slug=slug,
        title_i18n=as_locale_map(title),
        description_i18n=as_locale_map(description),
        difficulty=difficulty,
        environment_type=environment_type,
        gns3_template_project_id=gns3_template_project_id,
    )
    db.add(lab)
    await db.flush()
    await db.refresh(lab)
    return lab


async def delete_lab(db: AsyncSession, slug: str) -> bool:
    """Deletes a lab from the DB by slug. Returns False if it doesn't exist."""
    lab = await get_lab_by_slug(db, slug)
    if lab is None:
        return False
    await db.delete(lab)
    return True


async def get_lab_by_slug(db: AsyncSession, slug: str) -> Lab | None:
    """Returns the lab by slug with its steps, or None."""
    result = await db.execute(select(Lab).options(selectinload(Lab.steps)).where(Lab.slug == slug))
    return result.scalar_one_or_none()


_UPDATE_SAFELIST = {
    "enabled",
    "gns3_template_project_id",
    "gns3_template_project_id_frr",
    "gns3_template_project_id_iosvl2",
}


async def update_lab(db: AsyncSession, slug: str, fields: dict) -> Lab | None:
    """Apply given Lab column fields and commit. None if missing."""
    lab = await get_lab_by_slug(db, slug)
    if lab is None:
        return None
    for key, value in fields.items():
        if key in _UPDATE_SAFELIST:
            setattr(lab, key, value)
    await db.commit()
    await db.refresh(lab)
    return lab


_VARIANT_COLUMN: dict[str, str] = {
    "default": "gns3_template_project_id",
    "frr": "gns3_template_project_id_frr",
    "iosvl2": "gns3_template_project_id_iosvl2",
}


async def set_lab_template(
    db: AsyncSession, slug: str, template_project_id: str, variant: str = "default"
) -> Lab:
    """Binds a GNS3 template_project_id to the lab for the given environment variant.

    variant: "default" | "frr" | "iosvl2"
    Returns the updated Lab. Raises LocalizedError(404) for an unknown slug.
    """
    lab = await db.get(Lab, slug)
    if lab is None:
        raise LocalizedError("error.lab.not_found", status_code=404)
    column = _VARIANT_COLUMN[variant]
    setattr(lab, column, template_project_id)
    await db.flush()
    await db.refresh(lab)
    return lab


async def log_lab_problems() -> int:
    """Logs every lab whose declarations do not add up. Returns the problem count."""
    try:
        async with async_session() as db:
            labs = await get_all_labs(db)
        problems = audit_labs(labs, spec_slugs())
    except Exception:
        logger.warning("Lab readiness audit failed to run", exc_info=True)
        return 0

    for problem in problems:
        logger.warning("Lab readiness: %s [%s] %s", problem.slug, problem.kind, problem.detail)
    if problems:
        logger.warning("Lab readiness: %d problem(s) found", len(problems))
    return len(problems)
