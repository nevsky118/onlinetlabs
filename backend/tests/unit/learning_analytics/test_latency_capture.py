"""Latency capture: model, config flag, stage recording, and percentiles from the DB."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.config_model import LearningAnalyticsConfig
from models.cycle_latency_sample import CycleLatencySample

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(CycleLatencySample.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


class TestLatencyCapture:
    @autotest.num("1990")
    @autotest.external_id("a5513d05-9c62-4b7a-9a87-349b0b7f9359")
    @autotest.name("CycleLatencySample: table has the required columns")
    def test_a5513d05_model_columns(self):
        with autotest.step("Act+Assert: columns and table name"):
            cols = set(CycleLatencySample.__table__.columns.keys())
            assert_true(
                {"id", "session_id", "stage", "duration_ms", "ts", "created_at"} <= cols,
                f"required columns; got {cols}",
            )
            assert_equal(CycleLatencySample.__tablename__, "cycle_latency_samples", "table name")

    @autotest.num("1991")
    @autotest.external_id("947a4af6-c03b-4675-9baa-7a3f4d30855c")
    @autotest.name("Config: latency_capture_enabled defaults to False")
    def test_947a4af6_config_default(self):
        with autotest.step("Act+Assert: default is disabled"):
            assert_equal(
                LearningAnalyticsConfig().latency_capture_enabled, False, "defaults to False"
            )

    @autotest.num("1992")
    @autotest.external_id("6356775e-2bcf-49e5-998a-b10bbb964b45")
    @autotest.name("record_stage_latency + stage_percentiles: p50/p95/p99 from the DB")
    async def test_6356775e_record_and_aggregate(self):
        with autotest.step("Arrange: record 10 analysis-stage durations"):
            from learning_analytics.latency import record_stage_latency, stage_percentiles

            sf = await _sqlite_factory()
            async with sf() as db:
                for ms in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
                    await record_stage_latency(db, "s1", "analysis", float(ms))

        with autotest.step("Act+Assert: percentiles from the DB"):
            async with sf() as db:
                out = await stage_percentiles(db, "analysis", [50, 95, 99])
            assert_equal(out[50], 55.0, "p50 == 55.0 (Type 7)")
            assert_equal(out[95], 95.5, "p95 == 95.5 (Type 7)")

    @autotest.num("1993")
    @autotest.external_id("aa995048-f51f-4f5b-ae83-c23e1fcafab6")
    @autotest.name("stage_percentiles: stages are isolated")
    async def test_aa995048_stages_isolated(self):
        with autotest.step("Arrange: analysis=[100,100], intervention=[10]"):
            from learning_analytics.latency import record_stage_latency, stage_percentiles

            sf = await _sqlite_factory()
            async with sf() as db:
                await record_stage_latency(db, "s1", "analysis", 100.0)
                await record_stage_latency(db, "s1", "analysis", 100.0)
                await record_stage_latency(db, "s1", "intervention", 10.0)

        with autotest.step("Act+Assert: each stage is counted separately"):
            async with sf() as db:
                a = await stage_percentiles(db, "analysis", [50])
                i = await stage_percentiles(db, "intervention", [50])
            assert_equal(a[50], 100.0, "analysis p50 == 100")
            assert_equal(i[50], 10.0, "intervention p50 == 10")
