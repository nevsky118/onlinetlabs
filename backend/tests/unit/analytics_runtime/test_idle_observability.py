"""Test: ongoing silence accumulates idle_periods, the observer heartbeat does not."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from analytics.runtime.features import FeatureExtractor
from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


def _event(seconds_ago: float, action: str = "config", event_type: str = "action"):
    return SimpleNamespace(
        timestamp=datetime.now(tz=UTC) - timedelta(seconds=seconds_ago),
        event_type=event_type,
        action=action,
        component_id="n1",
        message=None,
        success=True,
        extra_data=None,
    )


class TestIdleObservability:
    @autotest.num("3011")
    @autotest.external_id("21640548-fc62-46ea-9d40-d92d13820566")
    @autotest.name("FeatureExtractor: ongoing silence counts as an idle period")
    def test_21640548_trailing_silence_counts_as_idle(self):
        with autotest.step("Arrange: two student actions, then a long silence"):
            events = [_event(400.0), _event(390.0)]
            extractor = FeatureExtractor(LearningAnalyticsConfig())

        with autotest.step("Act: compute features"):
            features = extractor.compute("s1", events)

        with autotest.step("Assert: the gap up to now is counted"):
            assert_true(features.idle_periods >= 1, f"idle_periods == {features.idle_periods}")

    @autotest.num("3012")
    @autotest.external_id("298d8946-1225-4dae-94a1-1118e6bb6cdb")
    @autotest.name("FeatureExtractor: observer heartbeat does not mask idle time")
    def test_298d8946_observer_heartbeat_excluded(self):
        with autotest.step("Arrange: silent student, observer polling every 25s"):
            events = [_event(400.0), _event(390.0)]
            events += [_event(age, action="check_failing") for age in (365.0, 340.0, 315.0, 290.0)]
            extractor = FeatureExtractor(LearningAnalyticsConfig())

        with autotest.step("Act: compute features"):
            features = extractor.compute("s1", events)

        with autotest.step("Assert: heartbeat gaps are not student activity"):
            assert_true(features.idle_periods >= 1, f"idle_periods == {features.idle_periods}")

    @autotest.num("3013")
    @autotest.external_id("f3f1cf3e-6a1c-4d0e-9a0f-4a4b6a2f9a11")
    @autotest.name("FeatureExtractor: recent activity yields no idle period")
    def test_f3f1cf3e_recent_activity_is_not_idle(self):
        with autotest.step("Arrange: two actions seconds apart, no silence"):
            events = [_event(6.0), _event(1.0)]
            extractor = FeatureExtractor(LearningAnalyticsConfig())

        with autotest.step("Act: compute features"):
            features = extractor.compute("s1", events)

        with autotest.step("Assert: no idle periods"):
            assert_equal(features.idle_periods, 0, "idle_periods == 0")
