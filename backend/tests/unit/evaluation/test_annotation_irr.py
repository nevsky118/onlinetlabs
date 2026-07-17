"""IRR-пайплайн: сохранение аннотаций коллаборантов + Cohen's kappa + gold-count."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from evaluation.real_loader import cohens_kappa
from models.regime_annotation import RegimeAnnotation

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(RegimeAnnotation.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


class TestAnnotationIRR:
    @autotest.num("1981")
    @autotest.external_id("0fb9b0b5-05ad-4fc0-ac19-b2e6eca9f2fa")
    @autotest.name("IRR: inter_rater_kappa совпадает с cohens_kappa по выровненным окнам")
    async def test_0fb9b0b5_kappa_matches_aligned(self):
        with autotest.step("Arrange: коллаборанты A и B размечают 4 окна, согласие 3/4"):
            from evaluation.annotation import inter_rater_kappa, save_annotation
            sf = await _sqlite_factory()
            a = ["idle", "idle", "productive", "stuck_on_step"]
            b = ["idle", "idle", "productive", "productive"]
            async with sf() as db:
                for i, (la, lb) in enumerate(zip(a, b)):
                    await save_annotation(db, "s1", "coderA", i, la)
                    await save_annotation(db, "s1", "coderB", i, lb)

        with autotest.step("Act: посчитать inter_rater_kappa(s1, A, B)"):
            async with sf() as db:
                k = await inter_rater_kappa(db, "s1", "coderA", "coderB")

        with autotest.step("Assert: равно cohens_kappa на тех же списках"):
            assert_equal(round(k, 6), round(cohens_kappa(a, b), 6), "kappa совпадает с эталоном")

    @autotest.num("1982")
    @autotest.external_id("5930bc24-9ed8-4368-a0f6-b2a181248fa7")
    @autotest.name("IRR: полное согласие → kappa == 1.0")
    async def test_5930bc24_perfect_agreement(self):
        with autotest.step("Arrange: A и B размечают одинаково"):
            from evaluation.annotation import inter_rater_kappa, save_annotation
            sf = await _sqlite_factory()
            labels = ["idle", "stuck_on_step", "productive"]
            async with sf() as db:
                for i, lbl in enumerate(labels):
                    await save_annotation(db, "s1", "A", i, lbl)
                    await save_annotation(db, "s1", "B", i, lbl)

        with autotest.step("Act+Assert: kappa == 1.0"):
            async with sf() as db:
                k = await inter_rater_kappa(db, "s1", "A", "B")
            assert_equal(k, 1.0, "полное согласие → 1.0")

    @autotest.num("1983")
    @autotest.external_id("446d4d47-65d5-4d54-ab6b-764e00d24ea0")
    @autotest.name("IRR: gold_label_count считает только is_gold, опц. по сессии")
    async def test_446d4d47_gold_count(self):
        with autotest.step("Arrange: 2 gold в s1, 1 обычная в s1, 1 gold в s2"):
            from evaluation.annotation import gold_label_count, save_annotation
            sf = await _sqlite_factory()
            async with sf() as db:
                await save_annotation(db, "s1", "gold", 0, "idle", is_gold=True)
                await save_annotation(db, "s1", "gold", 1, "productive", is_gold=True)
                await save_annotation(db, "s1", "A", 0, "idle", is_gold=False)
                await save_annotation(db, "s2", "gold", 0, "stuck_on_step", is_gold=True)

        with autotest.step("Act+Assert: всего gold==3, по s1==2"):
            async with sf() as db:
                total = await gold_label_count(db)
                s1 = await gold_label_count(db, session_id="s1")
            assert_equal(total, 3, "всего gold == 3")
            assert_equal(s1, 2, "gold в s1 == 2")
