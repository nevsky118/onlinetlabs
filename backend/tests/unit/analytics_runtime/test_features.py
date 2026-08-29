from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_greater,
    assert_greater_equal,
    assert_less_equal,
    assert_true,
)

from agents.identifier.schemas import SessionFeatures
from analytics.runtime.features import FeatureExtractor
from tests.settings.data.analytics_data import EventData, EventSequenceData

pytestmark = [pytest.mark.unit]


class TestFeatureExtractor:
    @autotest.num("530")
    @autotest.external_id("f9a0b1c2-d3e4-4f5a-8b6c-d7e8f9a0b1c2")
    @autotest.name("FeatureExtractor: empty event list")
    def test_f9a0b1c2_extract_from_empty_events(self):
        with autotest.step("Compute features from an empty list"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", [])

        with autotest.step("Check zero values"):
            assert_true(isinstance(features, SessionFeatures), "type SessionFeatures")
            assert_equal(features.events_total, 0, "0 events")
            assert_equal(features.avg_inter_action_latency, 0.0, "0 latency")
            assert_equal(features.error_repeat_count, 0, "0 error repeats")

    @autotest.num("531")
    @autotest.external_id("01a2b3c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c")
    @autotest.name("FeatureExtractor: average latency between actions")
    def test_01a2b3c4_avg_inter_action_latency(self):
        with autotest.step("Create 5 events at a 10s interval"):
            events = EventSequenceData(5, interval_seconds=10.0).events

        with autotest.step("Compute features"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Check latency ~10s"):
            assert_greater_equal(features.avg_inter_action_latency, 9.0, ">= 9")
            assert_less_equal(features.avg_inter_action_latency, 11.0, "<= 11")

    @autotest.num("532")
    @autotest.external_id("12b3c4d5-e6f7-4a8b-9c0d-1e2f3a4b5c6d")
    @autotest.name("FeatureExtractor: detects idle periods")
    def test_12b3c4d5_idle_periods_detected(self):
        with autotest.step("Create events with a gap > 60s"):
            now = datetime.now(tz=UTC)
            events = [
                EventData(id="e1", timestamp=now - timedelta(seconds=200)),
                EventData(id="e2", timestamp=now - timedelta(seconds=100)),
                EventData(id="e3", timestamp=now),
            ]

        with autotest.step("Compute features"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Check idle_periods >= 1"):
            assert_greater_equal(features.idle_periods, 1, "at least 1 idle period")

    @autotest.num("533")
    @autotest.external_id("23c4d5e6-f7a8-4b9c-8d0e-2f3a4b5c6d7e")
    @autotest.name("FeatureExtractor: counts repeating errors")
    def test_23c4d5e6_error_repeat_count(self):
        with autotest.step("Create 3 identical errors in a row"):
            now = datetime.now(tz=UTC)
            events = [
                EventData(
                    id="e1",
                    event_type="error",
                    action="cfg_err",
                    message="bad ip",
                    success=False,
                    timestamp=now - timedelta(seconds=30),
                ),
                EventData(
                    id="e2",
                    event_type="error",
                    action="cfg_err",
                    message="bad ip",
                    success=False,
                    timestamp=now - timedelta(seconds=20),
                ),
                EventData(
                    id="e3",
                    event_type="error",
                    action="cfg_err",
                    message="bad ip",
                    success=False,
                    timestamp=now - timedelta(seconds=10),
                ),
            ]

        with autotest.step("Compute features"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Check error_repeat_count >= 3"):
            assert_greater_equal(features.error_repeat_count, 3, "at least 3 repeats")

    @autotest.num("534")
    @autotest.external_id("34d5e6f7-a8b9-4c0d-9e1f-3a4b5c6d7e8f")
    @autotest.name("FeatureExtractor: entropy is 0 for uniform actions")
    def test_34d5e6f7_action_sequence_entropy_uniform(self):
        with autotest.step("Create 10 identical actions"):
            events = EventSequenceData(10, action="start_node").events

        with autotest.step("Compute features"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Check entropy = 0"):
            assert_equal(features.action_sequence_entropy, 0.0, "entropy = 0")

    @autotest.num("535")
    @autotest.external_id("45e6f7a8-b9c0-4d1e-af2a-4b5c6d7e8f9a")
    @autotest.name("FeatureExtractor: high entropy for diverse actions")
    def test_45e6f7a8_action_sequence_entropy_diverse(self):
        with autotest.step("Create 10 events with 5 different actions"):
            actions = ["start_node", "stop_node", "create_link", "delete_link", "reload_node"]
            now = datetime.now(tz=UTC)
            events = [
                EventData(
                    id=f"e{i}",
                    action=actions[i % len(actions)],
                    timestamp=now - timedelta(seconds=(10 - i) * 5),
                )
                for i in range(10)
            ]

        with autotest.step("Compute features"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Check entropy > 0.5"):
            assert_greater(features.action_sequence_entropy, 0.5, "entropy > 0.5")

    @autotest.num("536")
    @autotest.external_id("56f7a8b9-c0d1-4e2f-8a3b-5c6d7e8f9a0b")
    @autotest.name("FeatureExtractor: counts unique components")
    def test_56f7a8b9_components_touched(self):
        with autotest.step("Create events on 2 components"):
            now = datetime.now(tz=UTC)
            events = [
                EventData(id="e1", component_id="n1", timestamp=now - timedelta(seconds=20)),
                EventData(id="e2", component_id="n2", timestamp=now - timedelta(seconds=10)),
                EventData(id="e3", component_id="n1", timestamp=now),
            ]

        with autotest.step("Compute features"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Check components_touched = 2"):
            assert_equal(features.components_touched, 2, "2 unique components")

    @autotest.num("537")
    @autotest.external_id("67a8b9c0-d1e2-4f3a-9b4c-6d7e8f9a0b1c")
    @autotest.name("FeatureExtractor: error frequency per minute")
    def test_67a8b9c0_error_frequency(self):
        with autotest.step("Create 5 errors over 5 minutes"):
            now = datetime.now(tz=UTC)
            events = [
                EventData(
                    id=f"e{i}",
                    event_type="error",
                    action="err",
                    success=False,
                    message=f"err-{i}",
                    timestamp=now - timedelta(minutes=5 - i),
                )
                for i in range(5)
            ]

        with autotest.step("Compute features"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Check error_frequency ~1/min"):
            assert_greater_equal(features.error_frequency, 0.8, "frequency >= 0.8/min")
