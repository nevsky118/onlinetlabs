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


async def create_lab(
    db: AsyncSession, slug: str, title: str,
    description: str | None = None, difficulty: str = "beginner",
    environment_type: str = "none",
) -> Lab:
    lab = Lab(slug=slug, title=title, description=description,
              difficulty=difficulty, environment_type=environment_type)
    db.add(lab)
    await db.commit()
    await db.refresh(lab)
    return lab


async def delete_lab(db: AsyncSession, slug: str) -> bool:
    lab = await get_lab_by_slug(db, slug)
    if lab is None:
        return False
    await db.delete(lab)
    await db.commit()
    return True


async def get_lab_by_slug(db: AsyncSession, slug: str) -> Lab | None:
    result = await db.execute(
        select(Lab).options(selectinload(Lab.steps)).where(Lab.slug == slug)
    )
    return result.scalar_one_or_none()
