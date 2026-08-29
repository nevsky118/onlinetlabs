"""IRR pipeline: saving collaborator annotations + Cohen's kappa + gold-count."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from analytics.metrics.real_loader import cohens_kappa
from models.research import RegimeAnnotation

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(RegimeAnnotation.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


class TestAnnotationIRR:
    @autotest.num("1981")
    @autotest.external_id("0fb9b0b5-05ad-4fc0-ac19-b2e6eca9f2fa")
    @autotest.name("IRR: inter_rater_kappa matches cohens_kappa on aligned windows")
    async def test_0fb9b0b5_kappa_matches_aligned(self):
        with autotest.step("Arrange: coders A and B label 4 windows, 3/4 agreement"):
            from analytics.metrics.annotation import inter_rater_kappa, save_annotation

            sf = await _sqlite_factory()
            coder_a_labels = ["idle", "idle", "productive", "stuck_on_step"]
            coder_b_labels = ["idle", "idle", "productive", "productive"]
            async with sf() as db:
                for window, (label_a, label_b) in enumerate(zip(coder_a_labels, coder_b_labels)):
                    await save_annotation(db, "s1", "coderA", window, label_a)
                    await save_annotation(db, "s1", "coderB", window, label_b)

        with autotest.step("Act: compute inter_rater_kappa(s1, A, B)"):
            async with sf() as db:
                kappa = await inter_rater_kappa(db, "s1", "coderA", "coderB")

        with autotest.step("Assert: equals cohens_kappa on the same lists"):
            assert_equal(
                round(kappa, 6),
                round(cohens_kappa(coder_a_labels, coder_b_labels), 6),
                "kappa matches the reference",
            )

    @autotest.num("1982")
    @autotest.external_id("5930bc24-9ed8-4368-a0f6-b2a181248fa7")
    @autotest.name("IRR: full agreement → kappa == 1.0")
    async def test_5930bc24_perfect_agreement(self):
        with autotest.step("Arrange: A and B label identically"):
            from analytics.metrics.annotation import inter_rater_kappa, save_annotation

            sf = await _sqlite_factory()
            labels = ["idle", "stuck_on_step", "productive"]
            async with sf() as db:
                for value, lbl in enumerate(labels):
                    await save_annotation(db, "s1", "A", value, lbl)
                    await save_annotation(db, "s1", "B", value, lbl)

        with autotest.step("Act+Assert: kappa == 1.0"):
            async with sf() as db:
                kappa = await inter_rater_kappa(db, "s1", "A", "B")
            assert_equal(kappa, 1.0, "full agreement → 1.0")

    @autotest.num("1983")
    @autotest.external_id("446d4d47-65d5-4d54-ab6b-764e00d24ea0")
    @autotest.name("IRR: gold_label_count counts only is_gold, optionally by session")
    async def test_446d4d47_gold_count(self):
        with autotest.step("Arrange: 2 gold in s1, 1 regular in s1, 1 gold in s2"):
            from analytics.metrics.annotation import gold_label_count, save_annotation

            sf = await _sqlite_factory()
            async with sf() as db:
                await save_annotation(db, "s1", "gold", 0, "idle", is_gold=True)
                await save_annotation(db, "s1", "gold", 1, "productive", is_gold=True)
                await save_annotation(db, "s1", "A", 0, "idle", is_gold=False)
                await save_annotation(db, "s2", "gold", 0, "stuck_on_step", is_gold=True)

        with autotest.step("Act+Assert: total gold==3, s1==2"):
            async with sf() as db:
                total = await gold_label_count(db)
                s1 = await gold_label_count(db, session_id="s1")
            assert_equal(total, 3, "total gold == 3")
            assert_equal(s1, 2, "gold in s1 == 2")
