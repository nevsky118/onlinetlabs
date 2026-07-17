"""GroundTruthStore: true latent regime of the simulated student (reuses RegimeAnnotation as gold)."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.regime_annotation import RegimeAnnotation

pytestmark = [pytest.mark.unit]


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(RegimeAnnotation.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


class TestRecordTruth:
    @autotest.num("2032")
    @autotest.external_id("942a657b-724c-4db4-a38c-13532552041d")
    @autotest.name("ground_truth: истинный режим пишется как gold-аннотация коде́ра sim-truth")
    async def test_942a657b_record_truth_writes_sim_gold_annotation(self):
        with autotest.step("Arrange: чистая БД с таблицей аннотаций"):
            from simulation.ground_truth import record_truth

            factory = await _session_factory()

        with autotest.step("Act: фиксируем истинный режим окна"):
            async with factory() as db:
                await record_truth(db, "sess-1", window_index=3, true_regime="stuck_on_step")

        with autotest.step("Assert: записана одна gold-аннотация от sim-truth"):
            async with factory() as db:
                rows = (await db.execute(select(RegimeAnnotation))).scalars().all()
            assert_equal(len(rows), 1, "число аннотаций")
            annotation = rows[0]
            assert_equal(annotation.session_id, "sess-1", "session_id")
            assert_equal(annotation.coder_id, "sim-truth", "coder_id")
            assert_true(annotation.is_gold is True, "аннотация помечена как gold")
            assert_equal(annotation.regime_label, "stuck_on_step", "режим")
            assert_equal(annotation.window_index, 3, "индекс окна")
