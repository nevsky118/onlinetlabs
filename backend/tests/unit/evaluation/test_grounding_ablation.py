"""Grounded-vs-ungrounded ablation: пара вариантов помощи для слепой экспертной оценки."""

from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from agents.orchestrator.models import OrchestratorResponse
from config.config_model import LearningAnalyticsConfig
from models.grounding_comparison import GroundingComparison

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(GroundingComparison.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


def _resp(hint: str) -> OrchestratorResponse:
    return OrchestratorResponse(
        success=True, agent_used="tutor", agent_backend="openrouter",
        data={"hint": hint, "hint_level": 1}, metadata={"model": "m"}, error=None, latency_ms=10,
    )


class TestGroundingAblation:
    @autotest.num("1996")
    @autotest.external_id("68cea011-9964-47d8-bfa5-cd7dbf2422a7")
    @autotest.name("GroundingComparison: таблица содержит обязательные колонки")
    def test_68cea011_model_columns(self):
        with autotest.step("Act+Assert: колонки и имя таблицы"):
            cols = set(GroundingComparison.__table__.columns.keys())
            assert_true(
                {"id", "session_id", "grounded_text", "ungrounded_text", "ts", "created_at"} <= cols,
                f"обязательные колонки; есть {cols}",
            )
            assert_equal(GroundingComparison.__tablename__, "grounding_comparisons", "имя таблицы")

    @autotest.num("1997")
    @autotest.external_id("a25f1ca9-2f27-4f1d-90c5-fd74a198e8d3")
    @autotest.name("Config: grounding_ablation_enabled по умолчанию False")
    def test_a25f1ca9_config_default(self):
        with autotest.step("Act+Assert: дефолт выключен"):
            assert_equal(LearningAnalyticsConfig().grounding_ablation_enabled, False, "по умолчанию False")

    @autotest.num("1998")
    @autotest.external_id("eb6723d9-36ac-48c3-9a05-5f7b629cf103")
    @autotest.name("record_grounding_comparison: сохраняет оба варианта помощи")
    async def test_eb6723d9_record_pair(self):
        with autotest.step("Arrange+Act: записать пару grounded/ungrounded"):
            from evaluation.grounding import record_grounding_comparison
            sf = await _sqlite_factory()
            async with sf() as db:
                await record_grounding_comparison(db, "s1", "с контекстом среды", "только текст задачи")

        with autotest.step("Assert: 1 строка, оба текста сохранены"):
            async with sf() as db:
                rows = (await db.execute(select(GroundingComparison))).scalars().all()
            assert_equal(len(rows), 1, "1 сравнение")
            assert_equal(rows[0].grounded_text, "с контекстом среды", "grounded сохранён")
            assert_equal(rows[0].ungrounded_text, "только текст задачи", "ungrounded сохранён")

    @autotest.num("1999")
    @autotest.external_id("39734614-a49b-4cca-9b15-b51914bd9473")
    @autotest.name("generate_grounding_pair: два вызова orchestrator → пара текстов")
    async def test_39734614_generate_pair(self):
        with autotest.step("Arrange: orchestrator отдаёт grounded 'G', ungrounded 'U'"):
            from evaluation.grounding import generate_grounding_pair
            orch = AsyncMock()
            orch.intervene = AsyncMock(side_effect=[_resp("G"), _resp("U")])
            grounded_input = object()
            ungrounded_input = object()

        with autotest.step("Act: сгенерировать пару"):
            g, u = await generate_grounding_pair(orch, grounded_input, ungrounded_input)

        with autotest.step("Assert: тексты пары и два вызова"):
            assert_equal(g, "G", "grounded текст")
            assert_equal(u, "U", "ungrounded текст")
            assert_equal(orch.intervene.await_count, 2, "orchestrator вызван дважды")
