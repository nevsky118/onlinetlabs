"""Sync MDX frontmatter into database Course/Lab tables.

Usage: python -m scripts.sync_content
Or:    make sync-content
"""

import asyncio
import re
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session
from models.course import Course
from models.lab import Lab


CONTENT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "content"


def parse_frontmatter(file_path: Path) -> dict | None:
    text = file_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    return yaml.safe_load(match.group(1))


async def sync_courses(db: AsyncSession) -> int:
    courses_dir = CONTENT_DIR / "courses"
    if not courses_dir.exists():
        return 0
    count = 0
    for mdx_file in sorted(courses_dir.glob("*.mdx")):
        fm = parse_frontmatter(mdx_file)
        if fm is None:
            continue
        slug = mdx_file.stem
        result = await db.execute(select(Course).where(Course.slug == slug))
        course = result.scalar_one_or_none()
        if course is None:
            course = Course(slug=slug)
            db.add(course)
        course.title = fm.get("title", slug)
        course.description = fm.get("description")
        course.difficulty = fm.get("difficulty", "beginner")
        course.meta = {"tags": fm.get("tags", []), "tasks": fm.get("tasks")}
        count += 1
    await db.commit()
    return count


async def sync_labs(db: AsyncSession) -> int:
    labs_dir = CONTENT_DIR / "labs"
    if not labs_dir.exists():
        return 0
    count = 0
    for mdx_file in sorted(labs_dir.glob("*.mdx")):
        fm = parse_frontmatter(mdx_file)
        if fm is None:
            continue
        slug = mdx_file.stem
        result = await db.execute(select(Lab).where(Lab.slug == slug))
        lab = result.scalar_one_or_none()
        if lab is None:
            lab = Lab(slug=slug)
            db.add(lab)
        lab.title = fm.get("title", slug)
        lab.description = fm.get("description")
        lab.difficulty = fm.get("difficulty", "beginner")
        lab.meta = {"tags": fm.get("tags", []), "tasks": fm.get("tasks")}
        count += 1
    await db.commit()
    return count


async def main():
    async with async_session() as db:
        courses = await sync_courses(db)
        labs = await sync_labs(db)
    print(f"Synced {courses} courses, {labs} labs")


if __name__ == "__main__":
    asyncio.run(main())
