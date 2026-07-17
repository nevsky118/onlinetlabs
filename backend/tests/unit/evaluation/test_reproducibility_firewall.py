"""Firewall: reproducibility bundle excludes data from is_simulated users."""

from datetime import UTC, datetime

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.intervention_decision import InterventionDecision
from models.regime_annotation import RegimeAnnotation
from models.session import LearningSession
from models.user import User

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(LearningSession.__table__.create)
        await conn.run_sync(InterventionDecision.__table__.create)
        await conn.run_sync(RegimeAnnotation.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


class TestReproducibilityFirewall:
    @autotest.num("2010")
    @autotest.external_id("dc7d6b51-9331-4c12-ad0c-6b7185638582")
    @autotest.name("Firewall: bundle не включает точки решения и gold сим-юзеров")
    async def test_dc7d6b51_bundle_excludes_simulated(self):
        with autotest.step("Arrange: реальный и сим юзер, у каждого сессия/решение/gold"):
            from evaluation.reproducibility import build_reproducibility_bundle

            sf = await _sqlite_factory()
            now = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
            async with sf() as db:
                db.add(User(id="u-real", email="r@t.local", is_simulated=False))
                db.add(User(id="u-sim", email="s@t.local", is_simulated=True))
                db.add(LearningSession(id="s-real", user_id="u-real", lab_slug="l", started_at=now))
                db.add(LearningSession(id="s-sim", user_id="u-sim", lab_slug="l", started_at=now))
                for sid, uid in [("s-real", "u-real"), ("s-sim", "u-sim")]:
                    db.add(
                        InterventionDecision(
                            id=f"d-{uid}",
                            session_id=sid,
                            user_id=uid,
                            lab_slug="l",
                            spell_id="sp",
                            ts=now,
                            regime="idle",
                            dwell_seconds=1.0,
                            t_k_applied=0.0,
                            assignment="intervene",
                        )
                    )
                    db.add(
                        RegimeAnnotation(
                            id=f"a-{uid}",
                            session_id=sid,
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

        with autotest.step("Assert: только реальные данные (сим отрезаны)"):
            assert_equal(len(bundle["intervention_decisions"]), 1, "1 решение (реальное)")
            assert_equal(len(bundle["regime_annotations"]), 1, "1 аннотация (реальная)")
            assert_equal(bundle["gold_label_count"], 1, "1 gold (реальный)")
