"""Grounding ablation: hook for _maybe_grounding_ablation into dispatch (gated)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from agents.orchestrator.schemas import InterventionInput, OrchestratorResponse
from analytics.runtime.monitor import PendingIntervention, SessionMonitor
from config.config_model import LearningAnalyticsConfig
from tests.settings.data.db_data import CapturingSessionData

pytestmark = [pytest.mark.unit]


def _resp(hint: str) -> OrchestratorResponse:
    return OrchestratorResponse(
        success=True,
        agent_used="tutor",
        agent_backend="openrouter",
        data={"hint": hint, "hint_level": 1},
        metadata={"model": "m"},
        error=None,
        latency_ms=10,
    )


def _monitor(cap, *, ablation_enabled, ungrounded_hint="U"):
    cfg = LearningAnalyticsConfig()
    cfg.grounding_ablation_enabled = ablation_enabled
    orch = MagicMock()
    orch.intervene = AsyncMock(return_value=_resp(ungrounded_hint))
    monitor = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=lambda: cap,
        orchestrator=orch,
        learning_analytics_config=cfg,
        gateway=MagicMock(),
    )
    monitor._session_id = "s1"
    monitor._user_id = "u1"
    monitor._lab_slug = "lab-gns3"
    return monitor


def _pending(grounded_hint="G") -> PendingIntervention:
    payload = InterventionInput(
        session_id="s1",
        user_id="u1",
        intervention_type="hint",
        context={"agent_context": {"topology": "1 router"}},
    )
    return PendingIntervention(
        analysis=MagicMock(),
        features=MagicMock(),
        payload=payload,
        response=_resp(grounded_hint),
    )


def _comparisons(cap):
    return [row for row in cap.added if type(row).__name__ == "GroundingComparison"]


class TestGroundingWiring:
    @autotest.num("2000")
    @autotest.external_id("924bbef8-32d3-4e51-9c08-9eb9e778e2d9")
    @autotest.name("Ablation on: generates an ungrounded variant and records a pair")
    async def test_924bbef8_records_pair_when_enabled(self):
        with autotest.step(
            "Arrange: monitor ablation on, pending with grounded='G', orch returns 'U'"
        ):
            cap = CapturingSessionData()
            monitor = _monitor(cap, ablation_enabled=True, ungrounded_hint="U")
            pending = _pending(grounded_hint="G")

        with autotest.step("Act: _maybe_grounding_ablation"):
            await monitor._maybe_grounding_ablation(pending)

        with autotest.step("Assert: G/U pair recorded, orchestrator called once (ungrounded)"):
            comps = _comparisons(cap)
            assert_equal(len(comps), 1, f"1 comparison; got {len(comps)}")
            assert_equal(comps[0].grounded_text, "G", "grounded from the dispatch response")
            assert_equal(comps[0].ungrounded_text, "U", "ungrounded from the retry generation")
            assert_equal(
                monitor._orchestrator.intervene.await_count, 1, "1 extra call (ungrounded)"
            )

    @autotest.num("2001")
    @autotest.external_id("a722d45e-b05a-41ef-8938-47d49938e0b3")
    @autotest.name("Ablation off: pair is NOT recorded, no extra generation")
    async def test_a722d45e_noop_when_disabled(self):
        with autotest.step("Arrange: monitor ablation off"):
            cap = CapturingSessionData()
            monitor = _monitor(cap, ablation_enabled=False)
            pending = _pending()

        with autotest.step("Act: _maybe_grounding_ablation"):
            await monitor._maybe_grounding_ablation(pending)

        with autotest.step("Assert: zero comparisons, orchestrator not called"):
            assert_equal(len(_comparisons(cap)), 0, "disabled → 0 comparisons")
            assert_equal(monitor._orchestrator.intervene.await_count, 0, "no extra generation")
