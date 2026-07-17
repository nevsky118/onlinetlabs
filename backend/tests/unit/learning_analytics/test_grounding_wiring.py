"""Grounding-ablation: врезка _maybe_grounding_ablation в dispatch (gated)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from agents.orchestrator.models import InterventionInput, OrchestratorResponse
from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import PendingIntervention, SessionMonitor

pytestmark = [pytest.mark.unit]


class _Cap:
    def __init__(self): self.added = []
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def add(self, obj): self.added.append(obj)
    async def commit(self): pass


def _resp(hint: str) -> OrchestratorResponse:
    return OrchestratorResponse(
        success=True, agent_used="tutor", agent_backend="openrouter",
        data={"hint": hint, "hint_level": 1}, metadata={"model": "m"}, error=None, latency_ms=10,
    )


def _monitor(cap, *, ablation_enabled, ungrounded_hint="U"):
    cfg = LearningAnalyticsConfig()
    cfg.grounding_ablation_enabled = ablation_enabled
    orch = MagicMock()
    orch.intervene = AsyncMock(return_value=_resp(ungrounded_hint))
    m = SessionMonitor(
        mcp_client=MagicMock(), db_factory=lambda: cap, orchestrator=orch,
        learning_analytics_config=cfg, gateway=MagicMock(),
    )
    m._session_id = "s1"
    m._user_id = "u1"
    m._lab_slug = "lab-gns3"
    return m


def _pending(grounded_hint="G") -> PendingIntervention:
    payload = InterventionInput(
        session_id="s1", user_id="u1", intervention_type="hint",
        context={"agent_context": {"topology": "1 router"}},
    )
    return PendingIntervention(
        analysis=MagicMock(), features=MagicMock(), payload=payload,
        response=_resp(grounded_hint),
    )


def _comparisons(cap):
    return [o for o in cap.added if type(o).__name__ == "GroundingComparison"]


class TestGroundingWiring:
    @autotest.num("2000")
    @autotest.external_id("924bbef8-32d3-4e51-9c08-9eb9e778e2d9")
    @autotest.name("Ablation on: генерирует ungrounded-вариант и пишет пару")
    async def test_924bbef8_records_pair_when_enabled(self):
        with autotest.step("Arrange: монитор ablation on, pending с grounded='G', orch отдаёт 'U'"):
            cap = _Cap()
            m = _monitor(cap, ablation_enabled=True, ungrounded_hint="U")
            pending = _pending(grounded_hint="G")

        with autotest.step("Act: _maybe_grounding_ablation"):
            await m._maybe_grounding_ablation(pending)

        with autotest.step("Assert: записана пара G/U, orchestrator вызван 1 раз (ungrounded)"):
            comps = _comparisons(cap)
            assert_equal(len(comps), 1, f"1 сравнение; получено {len(comps)}")
            assert_equal(comps[0].grounded_text, "G", "grounded из ответа dispatch")
            assert_equal(comps[0].ungrounded_text, "U", "ungrounded из повторной генерации")
            assert_equal(m._orchestrator.intervene.await_count, 1, "1 доп. вызов (ungrounded)")

    @autotest.num("2001")
    @autotest.external_id("a722d45e-b05a-41ef-8938-47d49938e0b3")
    @autotest.name("Ablation off: пара НЕ пишется, доп. генерации нет")
    async def test_a722d45e_noop_when_disabled(self):
        with autotest.step("Arrange: монитор ablation off"):
            cap = _Cap()
            m = _monitor(cap, ablation_enabled=False)
            pending = _pending()

        with autotest.step("Act: _maybe_grounding_ablation"):
            await m._maybe_grounding_ablation(pending)

        with autotest.step("Assert: ноль сравнений, orchestrator не вызван"):
            assert_equal(len(_comparisons(cap)), 0, "выключено → 0 сравнений")
            assert_equal(m._orchestrator.intervene.await_count, 0, "доп. генерации нет")
