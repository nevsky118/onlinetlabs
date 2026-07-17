"""Task 1: sync_content tests, environment_type, CONTENT_DIR, idempotent upsert."""

import importlib.util
import textwrap
from pathlib import Path

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.lab import Lab

pytestmark = [pytest.mark.unit]

# Direct import from repo root/scripts/sync_content.py, bypassing backend/scripts/
_SYNC_CONTENT_PATH = Path(__file__).resolve().parents[4] / "scripts" / "sync_content.py"
_spec = importlib.util.spec_from_file_location("sync_content_top", _SYNC_CONTENT_PATH)
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)


async def _make_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Lab.__table__.create)
    return engine


def _write_lab_mdx(labs_dir: Path, slug: str, environment: str = "gns3") -> None:
    lab_dir = labs_dir / slug
    lab_dir.mkdir(parents=True, exist_ok=True)
    (lab_dir / "index.mdx").write_text(
        textwrap.dedent(f"""\
            ---
            title: Demo Lab
            environment: {environment}
            difficulty: easy
            ---
            ## Content
        """),
        encoding="utf-8",
    )


class TestSyncContent:
    @autotest.num("1824")
    @autotest.external_id("9b9e4305-4f22-479f-9635-fc5b1a87e1e9")
    @autotest.name("sync_content: environment_type проставляется из frontmatter")
    async def test_9b9e4305_environment_type_from_frontmatter(self, tmp_path, monkeypatch):
        labs_dir = tmp_path / "labs"
        _write_lab_mdx(labs_dir, "demo-lab", environment="gns3")
        monkeypatch.setattr(sc, "CONTENT_DIR", tmp_path)

        engine = await _make_db()
        factory = async_sessionmaker(engine, expire_on_commit=False)

        with autotest.step("Act: sync_labs на tmp content"):
            async with factory() as db:
                count = await sc.sync_labs(db)

        with autotest.step("Assert: одна лаба создана"):
            assert_equal(count, 1, "count=1")

        with autotest.step("Assert: environment_type == gns3"):
            async with factory() as db:
                lab = await db.get(Lab, "demo-lab")
            assert_true(lab is not None, "лаба найдена")
            assert_equal(lab.environment_type, "gns3", "environment_type=gns3")

        await engine.dispose()

    @autotest.num("1825")
    @autotest.external_id("b1dc0f5d-af40-46b6-86fb-c96091c23529")
    @autotest.name("sync_content: повторный прогон не создаёт дубль (idempotent upsert)")
    async def test_b1dc0f5d_idempotent_upsert(self, tmp_path, monkeypatch):
        labs_dir = tmp_path / "labs"
        _write_lab_mdx(labs_dir, "demo-lab", environment="gns3")
        monkeypatch.setattr(sc, "CONTENT_DIR", tmp_path)

        engine = await _make_db()
        factory = async_sessionmaker(engine, expire_on_commit=False)

        with autotest.step("Act: запустить sync_labs дважды"):
            async with factory() as db:
                await sc.sync_labs(db)
            async with factory() as db:
                await sc.sync_labs(db)

        with autotest.step("Assert: ровно одна строка в таблице"):
            from sqlalchemy import func, select

            async with factory() as db:
                result = await db.execute(select(func.count()).select_from(Lab))
                row_count = result.scalar()
            assert_equal(row_count, 1, "ровно 1 строка после двух прогонов")

        with autotest.step("Assert: environment_type == gns3 после второго прогона"):
            async with factory() as db:
                lab = await db.get(Lab, "demo-lab")
            assert_equal(lab.environment_type, "gns3", "environment_type=gns3")

        await engine.dispose()
