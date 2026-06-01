# E2E (Tier 2): REPEATING_ERRORS детектится и шлётся интервенция через gateway.

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("pydantic_ai")  # Tier 2: бежит только в backend-venv, иначе module-level skip

from autotests.settings.reports import autotest


def _error_events(n: int):
    from models.behavioral_event import BehavioralEvent
    now = datetime.now(tz=timezone.utc)
    return [
        BehavioralEvent(
            id=f"e{i}", session_id="s1", user_id="u1", lab_slug="autotest-lab",
            timestamp=now, event_type="error", action="cmd",
            success=False, message="same error", severity="error",
        )
        for i in range(n)
    ]


@pytest.mark.e2e
@pytest.mark.asyncio
class TestStruggleInterventionE2E:
    @autotest.num("711")
    @autotest.external_id("e1f2a3b4-c5d6-7890-efab-711000000001")
    @autotest.name("E2E: 3 одинаковые ошибки -> struggle REPEATING_ERRORS -> HINT")
    async def test_e1f2a3b4_detection(self):
        from agents.analytics.agent import AnalyticsAgent
        from agents.analytics.models import StruggleType, SuggestedIntervention
        from config.config_model import LearningAnalyticsConfig
        from config.env_config_loader import EnvConfigLoader
        from learning_analytics.features import FeatureExtractor

        backend_config = EnvConfigLoader().load("../backend/local.env")
        la_cfg = LearningAnalyticsConfig()
        with autotest.step("FeatureExtractor по 3 одинаковым ошибкам"):
            features = FeatureExtractor(la_cfg).compute("s1", _error_events(3))
            assert features.error_repeat_count >= la_cfg.error_repeat_threshold

        with autotest.step("AnalyticsAgent детектит REPEATING_ERRORS -> HINT"):
            result = AnalyticsAgent(backend_config, None).analyze_session(features, la_cfg)
            assert result.struggle_detected is True
            assert result.struggle_type == StruggleType.REPEATING_ERRORS
            assert result.suggested_intervention == SuggestedIntervention.HINT

    @autotest.num("712")
    @autotest.external_id("f1a2b3c4-d5e6-7890-fabc-712000000002")
    @autotest.name("E2E: monitor._run_analysis шлёт интервенцию в gateway")
    async def test_f1a2b3c4_intervention_sent(self):
        from agents.analytics.agent import AnalyticsAgent
        from config.config_model import LearningAnalyticsConfig
        from config.env_config_loader import EnvConfigLoader
        from learning_analytics.context import AgentContext
        from learning_analytics.features import FeatureExtractor
        from learning_analytics.monitor import SessionMonitor

        backend_config = EnvConfigLoader().load("../backend/local.env")
        la_cfg = LearningAnalyticsConfig()
        events = _error_events(3)

        class _Result:
            def scalars(self): return self
            def all(self): return events

        class _DBSession:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def execute(self, *a, **k): return _Result()

        def _db_factory(): return _DBSession()

        gateway = MagicMock()
        gateway.send_intervention = AsyncMock()

        orchestrator = MagicMock()
        orchestrator.intervene = AsyncMock(return_value=MagicMock(
            success=True,
            data={"hint": "проверь конфиг VLAN", "hint_level": 1},
            agent_used="hint",
            agent_backend="yandex",
            latency_ms=100,
            error=None,
            metadata={"experiment_group": "group_a", "model": "yandex-gpt", "provider": "yandex", "error_code": None},
        ))

        monitor = SessionMonitor(
            mcp_client=MagicMock(),
            db_factory=_db_factory,
            orchestrator=orchestrator,
            learning_analytics_config=la_cfg,
            gateway=gateway,
        )

        # Set session state (mirrors start_session)
        monitor._session_id = "s1"
        monitor._user_id = "u1"
        monitor._lab_slug = "autotest-lab"
        monitor._ctx = MagicMock()
        monitor._last_intervention_at = None

        # Replace heavy sub-components with controlled mocks
        monitor._feature_extractor = FeatureExtractor(la_cfg)
        monitor._analytics_agent = AnalyticsAgent(backend_config, None)

        stub_context = AgentContext(
            topology_summary="",
            recent_errors=[],
            recent_actions=[],
            struggle_type="repeating_errors",
            dominant_error="same error",
            features_summary="3 events",
        )
        monitor._context_builder = MagicMock()
        monitor._context_builder.build = AsyncMock(return_value=stub_context)

        monitor._log_intervention = AsyncMock()

        with autotest.step("Запускаем один цикл анализа"):
            await monitor._run_analysis()

        with autotest.step("Интервенция отправлена в gateway"):
            gateway.send_intervention.assert_awaited()
            args = gateway.send_intervention.await_args.args
            assert args[0] == "s1"
