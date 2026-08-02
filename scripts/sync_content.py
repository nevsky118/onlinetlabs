"""Sync MDX frontmatter into database Course/Lab tables.

Usage: python -m scripts.sync_content
Or:    make sync-content
"""

import asyncio
import os
import re
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session
from i18n import DEFAULT_LOCALE, LOCALES, as_locale_map
from models.course import Course
from models.lab import Lab

CONTENT_DIR = (
    Path(os.environ["CONTENT_DIR"])
    if os.environ.get("CONTENT_DIR")
    else Path(__file__).resolve().parent.parent / "frontend" / "apps" / "web" / "content"
)


def parse_frontmatter(file_path: Path) -> dict | None:
    text = file_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    return yaml.safe_load(match.group(1))


def localized_frontmatter(directory: Path, stem: str) -> dict[str, dict]:
    """Frontmatter per locale from <stem>.<locale>.mdx files. Missing locales are omitted."""
    found = {}
    for locale in LOCALES:
        path = directory / f"{stem}.{locale}.mdx"
        if not path.exists():
            continue
        parsed = parse_frontmatter(path)
        if parsed is not None:
            found[locale] = parsed
    return found


def field_map(per_locale: dict[str, dict], field: str, default: str | None = None) -> dict | None:
    """Locale map for one frontmatter field, empty values dropped."""
    return as_locale_map({loc: fm.get(field, default) for loc, fm in per_locale.items()})


async def sync_courses(db: AsyncSession) -> int:
    courses_dir = CONTENT_DIR / "courses"
    if not courses_dir.exists():
        return 0
    count = 0
    stems = sorted({path.name.split(".")[0] for path in courses_dir.glob("*.*.mdx")})
    for slug in stems:
        per_locale = localized_frontmatter(courses_dir, slug)
        if not per_locale:
            continue
        result = await db.execute(select(Course).where(Course.slug == slug))
        course = result.scalar_one_or_none()
        if course is None:
            course = Course(slug=slug)
            db.add(course)
        course.title_i18n = field_map(per_locale, "title", slug)
        course.description_i18n = field_map(per_locale, "description")
        default_fm = per_locale.get(DEFAULT_LOCALE) or next(iter(per_locale.values()))
        course.difficulty = default_fm.get("difficulty", "beginner")
        course.meta = {"tags": default_fm.get("tags", []), "tasks": default_fm.get("tasks")}
        count += 1
    await db.commit()
    return count


async def sync_labs(db: AsyncSession) -> int:
    labs_dir = CONTENT_DIR / "labs"
    if not labs_dir.exists():
        return 0
    count = 0
    for lab_dir in sorted(p for p in labs_dir.glob("*/") if p.is_dir()):
        slug = lab_dir.name
        per_locale = localized_frontmatter(lab_dir, "index")
        if not per_locale:
            continue
        result = await db.execute(select(Lab).where(Lab.slug == slug))
        lab = result.scalar_one_or_none()
        if lab is None:
            lab = Lab(slug=slug)
            db.add(lab)
        lab.title_i18n = field_map(per_locale, "title", slug)
        lab.description_i18n = field_map(per_locale, "description")
        default_fm = per_locale.get(DEFAULT_LOCALE) or next(iter(per_locale.values()))
        lab.difficulty = default_fm.get("difficulty", "beginner")
        lab.environment_type = default_fm.get("environment", "none")
        lab.meta = {
            "tags": default_fm.get("tags", []),
            "tasks": default_fm.get("tasks"),
            "skill": default_fm.get("skill"),
        }
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
