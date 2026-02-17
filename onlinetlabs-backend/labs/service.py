from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.lab import Lab


async def get_all_labs(db: AsyncSession, course_slug: str | None = None) -> list[Lab]:
    stmt = select(Lab)
    if course_slug is not None:
        stmt = stmt.where(Lab.course_slug == course_slug)
    stmt = stmt.order_by(Lab.order_in_course)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_lab_by_slug(db: AsyncSession, slug: str) -> Lab | None:
    result = await db.execute(
        select(Lab).options(selectinload(Lab.steps)).where(Lab.slug == slug)
    )
    return result.scalar_one_or_none()
