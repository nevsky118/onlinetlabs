import pytest
from datetime import datetime, timezone

from config.config_model import LearningAnalyticsConfig
from learning_analytics.collector import BehavioralCollector
from mcp_sdk.models import UserAction, LogEntry, ErrorEntry, LogLevel
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class TestBehavioralCollectorNormalization:
    @autotest.num("520")
    @autotest.external_id("b5c6d7e8-f9a0-4b1c-9d2e-f3a4b5c6d7e8")
    @autotest.name("BehavioralCollector: нормализация UserAction")
    def test_b5c6d7e8_normalize_user_action(self):
        with autotest.step("Создаём UserAction"):
            action = UserAction(
                timestamp=datetime.now(tz=timezone.utc),
                component_id="node-1",
                action="start_node",
                raw_command=None,
                success=True,
            )

        with autotest.step("Нормализуем в event dict"):
            event = BehavioralCollector.normalize_user_action(
                action, session_id="s1", user_id="u1", lab_slug="lab-1",
                component_types={"node-1": "qemu"},
            )

        with autotest.step("Проверяем поля"):
            assert_equal(event["event_type"], "action", "event_type = action")
            assert_equal(event["component_id"], "node-1", "component_id")
            assert_equal(event["component_type"], "qemu", "component_type из кэша")
            assert_true(event["success"], "success = True")

    @autotest.num("521")
    @autotest.external_id("c6d7e8f9-a0b1-4c2d-ae3f-a4b5c6d7e8f9")
    @autotest.name("BehavioralCollector: нормализация LogEntry")
    def test_c6d7e8f9_normalize_log_entry(self):
        with autotest.step("Создаём LogEntry"):
            log = LogEntry(
                timestamp=datetime.now(tz=timezone.utc),
                level=LogLevel.WARNING,
                message="Link flapping",
                source="node-1",
            )

        with autotest.step("Нормализуем в event dict"):
            event = BehavioralCollector.normalize_log_entry(
                log, session_id="s1", user_id="u1", lab_slug="lab-1",
            )

        with autotest.step("Проверяем поля"):
            assert_equal(event["event_type"], "log", "event_type = log")
            assert_equal(event["severity"], "warning", "severity = warning")
            assert_equal(event["message"], "Link flapping", "message")

    @autotest.num("522")
    @autotest.external_id("d7e8f9a0-b1c2-4d3e-8f4a-b5c6d7e8f9a0")
    @autotest.name("BehavioralCollector: нормализация ErrorEntry")
    def test_d7e8f9a0_normalize_error_entry(self):
        with autotest.step("Создаём ErrorEntry"):
            error = ErrorEntry(
                timestamp=datetime.now(tz=timezone.utc),
                level=LogLevel.ERROR,
                message="Interface Gi0/0 down",
                component_id="node-1",
            )

        with autotest.step("Нормализуем в event dict"):
            event = BehavioralCollector.normalize_error_entry(
                error, session_id="s1", user_id="u1", lab_slug="lab-1",
            )

        with autotest.step("Проверяем поля"):
            assert_equal(event["event_type"], "error", "event_type = error")
            assert_true(event["success"] is False, "success = False")
            assert_equal(event["severity"], "error", "severity = error")

    @autotest.num("523")
    @autotest.external_id("e8f9a0b1-c2d3-4e4f-9a5b-c6d7e8f9a0b1")
    @autotest.name("BehavioralCollector: дедупликация пропускает повторные события")
    def test_e8f9a0b1_dedup_skips_seen_events(self):
        with autotest.step("Создаём collector и генерируем ключ"):
            ts = datetime.now(tz=timezone.utc)
            collector = BehavioralCollector.__new__(BehavioralCollector)
            collector._seen = set()
            collector._cfg = LearningAnalyticsConfig()
            key = collector._dedup_key(ts, "start_node", "n1")

        with autotest.step("Первое событие — новое"):
            assert_true(collector._is_new(key), "первый раз = новое")

        with autotest.step("Второе событие — дубликат"):
            assert_true(not collector._is_new(key), "второй раз = дубликат")
