import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_false

from tests.settings.data.db_data import CapturingSessionData

pytestmark = [pytest.mark.unit]


class TestEscalation:
    @autotest.num("1242")
    @autotest.external_id("33841f1a-9dae-40f8-bff1-26c66accde50")
    @autotest.name("record_escalation: writes an event with type escalation and action=manual")
    async def test_33841f1a_record_escalation_writes_event(self):
        with autotest.step("Arrange: import record_escalation, a capturing db stub"):
            from sessions.services.escalation import record_escalation

            cap = CapturingSessionData()

        with autotest.step("Act: call record_escalation with source=manual"):
            await record_escalation(cap, "s1", "u1", "lab-1", source="manual")
            added = cap.added[0]
        with autotest.step("Assert: event_type and action are correct"):
            assert_equal(added.event_type, "escalation", "event_type = escalation")
            assert_equal(added.action, "manual", "action = manual")

    @autotest.num("1243")
    @autotest.external_id("4253a169-acd0-494f-b210-07482d6dea0d")
    @autotest.name(
        "record_escalation: source=objective → action=objective, success=False, severity=warn"
    )
    async def test_4253a169_record_escalation_objective_source(self):
        with autotest.step("Arrange: import record_escalation, a capturing db stub"):
            from sessions.services.escalation import record_escalation

            cap = CapturingSessionData()

        with autotest.step("Act: call record_escalation with source=objective"):
            await record_escalation(cap, "s2", "u2", "lab-2", source="objective")
            added = cap.added[0]
        with autotest.step("Assert: action, success and severity are correct"):
            assert_equal(added.action, "objective", "action = objective")
            assert_false(added.success, "success = False")
            assert_equal(added.severity, "warn", "severity = warn")
