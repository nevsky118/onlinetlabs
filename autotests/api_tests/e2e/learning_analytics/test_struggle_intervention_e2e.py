# E2E (Tier 2): REPEATING_ERRORS is detected and an intervention is sent through the gateway.

from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("pydantic_ai")  # Tier 2: runs only in the backend venv, otherwise a module-level skip

from autotests.settings.configuration.env_paths import env_file
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_equal, assert_greater_equal
from autotests.api.data.e2e.learning_analytics_data import RepeatedErrorEventsData


@pytest.mark.e2e
@pytest.mark.asyncio
class TestStruggleInterventionE2E:
    @autotest.num("3484")
    @autotest.external_id("0315969a-1f8c-4527-b83b-01e6dcc99a34")
    @autotest.name("E2E: 3 identical errors -> struggle REPEATING_ERRORS -> HINT")
    async def test_0315969a_detection(self):
        with autotest.step("Arrange: config and feature-extraction settings"):
            from agents.analytics.agent import AnalyticsAgent
            from agents.analytics.models import StruggleType, SuggestedIntervention
            from config.config_model import LearningAnalyticsConfig
            from config.env_config_loader import EnvConfigLoader
            from learning_analytics.features import FeatureExtractor

            backend_config = EnvConfigLoader().load(str(env_file("backend")))
            la_cfg = LearningAnalyticsConfig()
        with autotest.step("FeatureExtractor on 3 identical errors"):
            features = FeatureExtractor(la_cfg).compute("s1", RepeatedErrorEventsData(3).events)
            assert_greater_equal(features.error_repeat_count, la_cfg.error_repeat_threshold, "error repeat count")

        with autotest.step("AnalyticsAgent detects REPEATING_ERRORS -> HINT"):
            result = AnalyticsAgent(backend_config, None).analyze_session(features, la_cfg)
            assert_equal(result.struggle_detected, True, "struggle detected")
            assert_equal(result.struggle_type, StruggleType.REPEATING_ERRORS, "struggle type")
            assert_equal(result.suggested_intervention, SuggestedIntervention.HINT, "suggested intervention")

    @autotest.num("3485")
    @autotest.external_id("60fffc56-e8cf-4f59-a5f0-1f874f77195e")
    @autotest.name("E2E: monitor._run_analysis sends intervention to gateway")
    async def test_60fffc56_intervention_sent(self):
        with autotest.step("Arrange: analytics agent, gateway, orchestrator and monitor stubbed with a pending intervention"):
            from agents.analytics.agent import AnalyticsAgent
            from config.config_model import LearningAnalyticsConfig
            from config.env_config_loader import EnvConfigLoader
            from learning_analytics.context import AgentContext
            from learning_analytics.features import FeatureExtractor
            from learning_analytics.monitor import SessionMonitor

            backend_config = EnvConfigLoader().load(str(env_file("backend")))
            la_cfg = LearningAnalyticsConfig()
            events = RepeatedErrorEventsData(3).events

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

        with autotest.step("Run one analysis cycle"):
            await monitor._run_analysis()

        with autotest.step("Intervention sent to gateway"):
            gateway.send_intervention.assert_awaited()
            args = gateway.send_intervention.await_args.args
            assert_equal(args[0], "s1", "args[0]")
