"""Reproducibility bundle: anonymized export of real MRT data for re-analysis."""

import json
from datetime import UTC

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.intervention_decision import InterventionDecision
from models.regime_annotation import RegimeAnnotation

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    # firewall bundle joins users/learning_sessions (excludes is_simulated)
    from models.session import LearningSession
    from models.user import User

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(LearningSession.__table__.create)
        await conn.run_sync(InterventionDecision.__table__.create)
        await conn.run_sync(RegimeAnnotation.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


class TestReproducibility:
    @autotest.num("1986")
    @autotest.external_id("8795ed23-880c-4ad9-b4e4-f23cc003b301")
    @autotest.name("Repro-bundle: анонимизирует id, консистентен по таблицам, считает gold")
    async def test_8795ed23_bundle_anonymized_consistent(self):
        with autotest.step("Arrange: точка решения и gold-аннотация одной сессии s1/u1"):
            from datetime import datetime

            from evaluation.reproducibility import build_reproducibility_bundle

            sf = await _sqlite_factory()
            now = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
            async with sf() as db:
                db.add(
                    InterventionDecision(
                        id="d1",
                        session_id="s1",
                        user_id="u1",
                        lab_slug="lab",
                        spell_id="sp1",
                        ts=now,
                        regime="idle",
                        dwell_seconds=10.0,
                        t_k_applied=0.0,
                        assignment="intervene",
                    )
                )
                db.add(
                    RegimeAnnotation(
                        id="a1",
                        session_id="s1",
                        coder_id="gold",
                        window_index=0,
                        regime_label="idle",
                        is_gold=True,
                    )
                )
                await db.commit()

        with autotest.step("Act: собрать bundle"):
            async with sf() as db:
                bundle = await build_reproducibility_bundle(db)

        with autotest.step("Assert: структура, счётчики, анонимизация, консистентность id"):
            assert_equal(len(bundle["intervention_decisions"]), 1, "1 точка решения")
            assert_equal(len(bundle["regime_annotations"]), 1, "1 аннотация")
            assert_equal(bundle["gold_label_count"], 1, "1 gold")
            blob = json.dumps(bundle)
            assert_true("s1" not in blob and "u1" not in blob, "сырые id анонимизированы")
            assert_equal(
                bundle["intervention_decisions"][0]["session"],
                bundle["regime_annotations"][0]["session"],
                "один session → один анонимный id в обеих таблицах",
            )
