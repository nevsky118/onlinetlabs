from collections import OrderedDict
from datetime import UTC, datetime

import pytest
from mcp_sdk.models import ErrorEntry, LogEntry, LogLevel, UserAction
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from analytics.runtime.collector import BehavioralCollector
from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestBehavioralCollectorNormalization:
    @autotest.num("520")
    @autotest.external_id("b5c6d7e8-f9a0-4b1c-9d2e-f3a4b5c6d7e8")
    @autotest.name("BehavioralCollector: normalize UserAction")
    def test_b5c6d7e8_normalize_user_action(self):
        with autotest.step("Create a UserAction"):
            action = UserAction(
                timestamp=datetime.now(tz=UTC),
                component_id="node-1",
                action="start_node",
                raw_command=None,
                success=True,
            )

        with autotest.step("Normalize into an event dict"):
            event = BehavioralCollector.normalize_user_action(
                action,
                session_id="s1",
                user_id="u1",
                lab_slug="lab-1",
                component_types={"node-1": "qemu"},
            )

        with autotest.step("Check the fields"):
            assert_equal(event["event_type"], "action", "event_type = action")
            assert_equal(event["component_id"], "node-1", "component_id")
            assert_equal(event["component_type"], "qemu", "component_type from the cache")
            assert_true(event["success"], "success = True")

    @autotest.num("521")
    @autotest.external_id("c6d7e8f9-a0b1-4c2d-ae3f-a4b5c6d7e8f9")
    @autotest.name("BehavioralCollector: normalize LogEntry")
    def test_c6d7e8f9_normalize_log_entry(self):
        with autotest.step("Create a LogEntry"):
            log = LogEntry(
                timestamp=datetime.now(tz=UTC),
                level=LogLevel.WARNING,
                message="Link flapping",
                source="node-1",
            )

        with autotest.step("Normalize into an event dict"):
            event = BehavioralCollector.normalize_log_entry(
                log,
                session_id="s1",
                user_id="u1",
                lab_slug="lab-1",
            )

        with autotest.step("Check the fields"):
            assert_equal(event["event_type"], "log", "event_type = log")
            assert_equal(event["severity"], "warning", "severity = warning")
            assert_equal(event["message"], "Link flapping", "message")

    @autotest.num("522")
    @autotest.external_id("d7e8f9a0-b1c2-4d3e-8f4a-b5c6d7e8f9a0")
    @autotest.name("BehavioralCollector: normalize ErrorEntry")
    def test_d7e8f9a0_normalize_error_entry(self):
        with autotest.step("Create an ErrorEntry"):
            error = ErrorEntry(
                timestamp=datetime.now(tz=UTC),
                level=LogLevel.ERROR,
                message="Interface Gi0/0 down",
                component_id="node-1",
            )

        with autotest.step("Normalize into an event dict"):
            event = BehavioralCollector.normalize_error_entry(
                error,
                session_id="s1",
                user_id="u1",
                lab_slug="lab-1",
            )

        with autotest.step("Check the fields"):
            assert_equal(event["event_type"], "error", "event_type = error")
            assert_true(event["success"] is False, "success = False")
            assert_equal(event["severity"], "error", "severity = error")

    @autotest.num("523")
    @autotest.external_id("e8f9a0b1-c2d3-4e4f-9a5b-c6d7e8f9a0b1")
    @autotest.name("BehavioralCollector: dedup skips repeated events")
    def test_e8f9a0b1_dedup_skips_seen_events(self):
        with autotest.step("Create a collector and generate a key"):
            ts = datetime.now(tz=UTC)
            collector = BehavioralCollector.__new__(BehavioralCollector)
            collector._seen = OrderedDict()
            collector._cfg = LearningAnalyticsConfig()
            key = collector._dedup_key(ts, "start_node", "n1")

        with autotest.step("First event is new"):
            assert_true(collector._is_new(key), "first time = new")

        with autotest.step("Second event is a duplicate"):
            assert_true(not collector._is_new(key), "second time = duplicate")
