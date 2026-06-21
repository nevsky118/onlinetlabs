"""Тест: open-loop arm A подавляет проактив, arm B отправляет интервенцию."""

import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from agents.analytics.models import StruggleType
from agents.orchestrator.models import OrchestratorResponse
from config.config_model import LearningAnalyticsConfig
from experiment.control_arm import ControlArm
from learning_analytics.monitor import SessionMonitor

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


class _Cap:
    """Перехватывающая db-сессия."""
    def __init__(self): self.added = []
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def add(self, obj): self.added.append(obj)
    async def commit(self): pass
    async def execute(self, stmt): return _ScalarResult(None)
    async def get(self, model, key): return None


class _ScalarResult:
    def __init__(self, v): self._v = v
    def scalar_one_or_none(self): return self._v
    def scalars(self): return self
    def all(self): return []


def _make_features():
    from agents.analytics.models import SessionFeatures
    return SessionFeatures(
        session_id="s1", computed_at=datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc),
        avg_inter_action_latency=10.0, action_rate_slope=0.0, idle_periods=1,
        total_active_time=120.0, time_on_current_step=60.0,
        error_repeat_count=2, error_repeat_rate=0.5, action_sequence_entropy=0.3,
        undo_redo_ratio=0.0, error_frequency=0.3, error_frequency_slope=0.0,
        unique_error_types=1, dominant_error=None, components_touched=1,
        action_diversity=0.2, events_total=10,
    )


def _make_difficulty():
    from agents.analytics.models import DifficultyRecommendation, StudentMetrics
    return DifficultyRecommendation(
        current_difficulty="beginner", recommended_difficulty="beginner",
        reasoning="ok",
        metrics=StudentMetrics(
            total_attempts=5, success_rate=0.6, avg_time_per_step=30.0, struggling_steps=[],
        ),
    )


def _make_analysis(*, struggle=True):
    from agents.analytics.models import AnalyticsResult, SuggestedIntervention
    return AnalyticsResult(
        struggle_detected=struggle,
        struggle_type=StruggleType.IDLE,
        confidence=0.9,
        suggested_intervention=SuggestedIntervention.HINT,
        difficulty_recommendation=_make_difficulty(),
        features=_make_features(),
    )


def _make_monitor(arm: ControlArm, cap: _Cap) -> SessionMonitor:
    cfg = LearningAnalyticsConfig()
    cfg.dwell_thresholds = {"idle": 0.0, "stuck_on_step": 0.0, "repeating_errors": 0.0, "trial_and_error": 0.0}
    orchestrator = MagicMock()
    orchestrator.intervene = AsyncMock(return_value=OrchestratorResponse(
        success=True, agent_used="tutor", agent_backend="openrouter",
        data={"hint": "test hint", "hint_level": 1}, metadata={"model": "m"}, error=None,
        latency_ms=10,
    ))
    gateway = MagicMock()
    gateway.send_intervention = AsyncMock()
    m = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=lambda: cap,
        orchestrator=orchestrator,
        learning_analytics_config=cfg,
        gateway=gateway,
        control_arm=arm,
    )
    m._session_id = "s1"
    m._user_id = "u1"
    m._lab_slug = "lab-gns3"
    m._ctx = MagicMock()
    m._session_model_id = None
    return m


@pytest.mark.asyncio
async def test_open_arm_logs_would_intervene():
    """Arm A: _log_would_intervene пишет событие would_intervene в БД."""
    cap = _Cap()
    m = _make_monitor(ControlArm.OPEN, cap)
    analysis = _make_analysis()

    await m._log_would_intervene(analysis)

    # orchestrator не вызывался
    m._orchestrator.intervene.assert_not_called()

    types = [getattr(o, "event_type", None) for o in cap.added]
    assert "would_intervene" in types, f"would_intervene не записан; types: {types}"

    wi = next(o for o in cap.added if getattr(o, "event_type", None) == "would_intervene")
    assert wi.action == "hint"
    assert wi.session_id == "s1"
    assert wi.user_id == "u1"
    assert wi.extra_data["control_arm"] == "open"
    assert wi.success is False


@pytest.mark.asyncio
async def test_open_arm_run_analysis_no_dispatch():
    """Arm A: после dwell_ready → _log_would_intervene, без dispatch."""
    cap = _Cap()
    m = _make_monitor(ControlArm.OPEN, cap)
    analysis = _make_analysis()

    fake_event = SimpleNamespace(
        timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc),
    )

    m._analytics_agent = MagicMock()
    m._analytics_agent.analyze_session = MagicMock(return_value=analysis)
    m._feature_extractor = MagicMock()
    m._feature_extractor.compute = MagicMock(return_value=_make_features())

    with patch.object(m, "_load_new_events", AsyncMock(return_value=[fake_event])):
        # dwell=0 >= T_k=0 → dwell_ready=True → arm OPEN → _log_would_intervene
        await m._run_analysis()

    m._orchestrator.intervene.assert_not_called()
    types = [getattr(o, "event_type", None) for o in cap.added]
    assert "would_intervene" in types, f"would_intervene не записан; types: {types}"


@pytest.mark.asyncio
async def test_closed_arm_dispatches_intervention():
    """Arm B: _decide_intervention + _dispatch_intervention вызывает orchestrator."""
    cap = _Cap()
    m = _make_monitor(ControlArm.CLOSED, cap)
    analysis = _make_analysis()

    from learning_analytics.context import AgentContext
    m._context_builder.build = AsyncMock(return_value=AgentContext(
        topology_summary="1 router",
        recent_errors=[],
        recent_actions=[],
        struggle_type="idle",
        dominant_error=None,
        features_summary="",
    ))

    features = MagicMock()
    features.dominant_error = None
    features.error_repeat_count = 0

    pending = await m._decide_intervention(analysis, features)
    assert pending is not None

    await m._dispatch_intervention(pending)
    m._orchestrator.intervene.assert_called_once()


@pytest.mark.asyncio
async def test_would_intervene_respects_cooldown():
    """Arm A: второй вызов в период cooldown не пишет would_intervene."""
    cap = _Cap()
    m = _make_monitor(ControlArm.OPEN, cap)
    m._learning_analytics_config.cooldown_period = 60  # 60 сек cooldown
    analysis = _make_analysis()

    fake_event = SimpleNamespace(
        timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc),
    )

    m._analytics_agent = MagicMock()
    m._analytics_agent.analyze_session = MagicMock(return_value=analysis)
    m._feature_extractor = MagicMock()
    m._feature_extractor.compute = MagicMock(return_value=_make_features())

    with patch.object(m, "_load_new_events", AsyncMock(return_value=[fake_event])):
        await m._run_analysis()  # первый цикл — должен записать
        await m._run_analysis()  # второй цикл — cooldown ещё не истёк → пропуск

    wi_events = [o for o in cap.added if getattr(o, "event_type", None) == "would_intervene"]
    assert len(wi_events) == 1, f"ожидался 1 would_intervene, получено {len(wi_events)}"


def test_closed_arm_default():
    """Дефолтный control_arm=CLOSED — не ломает существующее поведение."""
    cfg = LearningAnalyticsConfig()
    m = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=MagicMock(),
        orchestrator=MagicMock(),
        learning_analytics_config=cfg,
    )
    assert m._control_arm == ControlArm.CLOSED
