from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.course import Course


async def get_all_courses(db: AsyncSession) -> list[Course]:
    result = await db.execute(select(Course).order_by(Course.order))
    return list(result.scalars().all())


async def get_course_by_slug(db: AsyncSession, slug: str) -> Course | None:
    result = await db.execute(
        select(Course).options(selectinload(Course.labs)).where(Course.slug == slug)
    )
    return result.scalar_one_or_none()
