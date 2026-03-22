import pytest
from datetime import datetime, timezone

from models.behavioral_event import BehavioralEvent
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none

pytestmark = [pytest.mark.unit]


class TestBehavioralEvent:
    @autotest.num("510")
    @autotest.external_id("e2f3a4b5-c6d7-4e8f-8a9b-c0d1e2f3a4b5")
    @autotest.name("BehavioralEvent: создание события действия")
    def test_e2f3a4b5_create_action_event(self):
        with autotest.step("Создаём событие типа action"):
            now = datetime.now(tz=timezone.utc)
            event = BehavioralEvent(
                session_id="sess-1",
                user_id="user-1",
                lab_slug="lab-ospf",
                timestamp=now,
                event_type="action",
                component_id="node-1",
                component_type="qemu",
                action="start_node",
                success=True,
            )

        with autotest.step("Проверяем поля"):
            assert_equal(event.event_type, "action", "event_type = action")
            assert_equal(event.session_id, "sess-1", "session_id")

    @autotest.num("511")
    @autotest.external_id("f3a4b5c6-d7e8-4f9a-ab0c-d1e2f3a4b5c6")
    @autotest.name("BehavioralEvent: создание события ошибки")
    def test_f3a4b5c6_create_error_event(self):
        with autotest.step("Создаём событие типа error"):
            now = datetime.now(tz=timezone.utc)
            event = BehavioralEvent(
                session_id="sess-1",
                user_id="user-1",
                lab_slug="lab-ospf",
                timestamp=now,
                event_type="error",
                action="config_error",
                success=False,
                severity="error",
                message="Interface not found",
            )

        with autotest.step("Проверяем поля"):
            assert_equal(event.event_type, "error", "event_type = error")
            assert_equal(event.severity, "error", "severity = error")

    @autotest.num("512")
    @autotest.external_id("a4b5c6d7-e8f9-4a0b-8c1d-e2f3a4b5c6d7")
    @autotest.name("BehavioralEvent: nullable поля по умолчанию None")
    def test_a4b5c6d7_nullable_fields(self):
        with autotest.step("Создаём событие с минимальными полями"):
            now = datetime.now(tz=timezone.utc)
            event = BehavioralEvent(
                session_id="sess-1",
                user_id="user-1",
                lab_slug="lab-ospf",
                timestamp=now,
                event_type="log",
                action="system_log",
                success=True,
            )

        with autotest.step("Проверяем nullable поля"):
            assert_is_none(event.component_id, "component_id is None")
            assert_is_none(event.component_type, "component_type is None")
            assert_is_none(event.severity, "severity is None")
            assert_is_none(event.message, "message is None")
            assert_is_none(event.extra_data, "extra_data is None")
