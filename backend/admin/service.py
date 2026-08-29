"""Queries behind the admin console: user list, lab rows, generic data browser."""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import String, cast, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.data_registry import TableSpec, serialize_row
from admin.schemas import AdminLab
from i18n import DEFAULT_LOCALE, resolve_localized
from kit.db import async_session
from labs.readiness import is_launchable
from labs.service import get_lab_by_slug
from models.identity import User, UserRole

# Deepest row the data browser will count or page to.
COUNT_CAP = 10_000


@dataclass(frozen=True)
class Page:
    """One page of rows plus the count that produced it."""

    rows: list
    total: int
    total_is_exact: bool = True


async def list_users(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    sort: str,
    order: Literal["asc", "desc"],
    search: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> Page:
    """Users filtered, sorted and paged."""
    col = getattr(User, sort)
    order_col = col.asc() if order == "asc" else col.desc()

    query = select(User)
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(User.name.ilike(pattern), User.email.ilike(pattern)))
    if role is not None:
        query = query.where(User.role == role.value)
    if is_active is not None:
        query = query.where(User.is_active.is_(is_active))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    rows = (
        (
            await db.execute(
                query.order_by(order_col).offset((page - 1) * page_size).limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return Page(rows=list(rows), total=total)


async def browse_table(
    db: AsyncSession,
    spec: TableSpec,
    *,
    page: int,
    page_size: int,
    sort: str | None,
    order: Literal["asc", "desc"],
    search: str | None = None,
) -> Page:
    """One page of a whitelisted log table, with a capped count.

    Counting the whole filtered set means a second full scan of a table that can
    hold millions of rows. Count only as far as the browser can page.
    """
    model = spec.model
    col = getattr(model, sort if sort in spec.sortable else spec.default_sort)
    order_col = col.asc() if order == "asc" else col.desc()

    conditions = []
    if search:
        pattern = f"%{search}%"
        conditions.append(
            or_(*[cast(getattr(model, c), String).ilike(pattern) for c in spec.searchable])
        )

    capped = select(literal(1)).select_from(model).where(*conditions).limit(COUNT_CAP).subquery()
    total = (await db.execute(select(func.count()).select_from(capped))).scalar() or 0

    offset = (page - 1) * page_size
    rows = (
        (
            await db.execute(
                select(model).where(*conditions).order_by(order_col).offset(offset).limit(page_size)
            )
        )
        .scalars()
        .all()
        if offset < COUNT_CAP
        else []
    )
    return Page(
        rows=[serialize_row(spec, r) for r in rows],
        total=total,
        total_is_exact=total < COUNT_CAP,
    )


def to_admin_lab(lab) -> AdminLab:
    """Serializes a Lab row for the admin console."""
    return AdminLab(
        slug=lab.slug,
        title=resolve_localized(lab.title_i18n, DEFAULT_LOCALE),
        enabled=lab.enabled,
        environment_type=lab.environment_type,
        course_slug=lab.course_slug,
        gns3_template_project_id=lab.gns3_template_project_id,
        gns3_template_project_id_frr=lab.gns3_template_project_id_frr,
        gns3_template_project_id_iosvl2=lab.gns3_template_project_id_iosvl2,
        # non-gns3 labs need no template
        template_ready=is_launchable(lab),
        template_status=(lab.meta or {}).get("template_status", "unknown"),
    )


async def rebuild_template(slug: str, gns3_client, session_factory=async_session) -> None:
    """Background task: builds the template and records the outcome on the lab."""
    try:
        template_id = await gns3_client.build_template(slug)
        new_status, tid = "ready", template_id
    except Exception:
        new_status, tid = "error", None
    async with session_factory() as session:
        lab = await get_lab_by_slug(session, slug)
        if lab is None:
            return
        if tid:
            lab.gns3_template_project_id = tid
        lab.meta = {**(lab.meta or {}), "template_status": new_status}
        await session.commit()
