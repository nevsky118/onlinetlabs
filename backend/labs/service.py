from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.lab import Lab


async def get_all_labs(db: AsyncSession, course_slug: str | None = None) -> list[Lab]:
    """Выбирает лабораторные работы из БД, опционально фильтруя по курсу, сортируя по порядку."""
    stmt = select(Lab)
    if course_slug is not None:
        stmt = stmt.where(Lab.course_slug == course_slug)
    stmt = stmt.order_by(Lab.order_in_course)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_lab(
    db: AsyncSession, slug: str, title: str,
    description: str | None = None, difficulty: str = "beginner",
    environment_type: str = "none", gns3_template_project_id: str | None = None,
) -> Lab:
    """Создаёт и сохраняет в БД новую лабораторную работу."""
    lab = Lab(slug=slug, title=title, description=description,
              difficulty=difficulty, environment_type=environment_type,
              gns3_template_project_id=gns3_template_project_id)
    db.add(lab)
    await db.commit()
    await db.refresh(lab)
    return lab


async def delete_lab(db: AsyncSession, slug: str) -> bool:
    """Удаляет лабораторную работу из БД по slug. Возвращает False, если её нет."""
    lab = await get_lab_by_slug(db, slug)
    if lab is None:
        return False
    await db.delete(lab)
    await db.commit()
    return True


async def get_lab_by_slug(db: AsyncSession, slug: str) -> Lab | None:
    """Возвращает лабораторную работу по slug вместе с её шагами или None."""
    result = await db.execute(
        select(Lab).options(selectinload(Lab.steps)).where(Lab.slug == slug)
    )
    return result.scalar_one_or_none()
