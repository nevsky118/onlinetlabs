import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_false

pytestmark = [pytest.mark.unit]


class _Cap:
    def __init__(self):
        self.added = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def add(self, o):
        self.added.append(o)

    async def commit(self):
        pass


class TestEscalation:
    @autotest.num("1242")
    @autotest.external_id("33841f1a-9dae-40f8-bff1-26c66accde50")
    @autotest.name("record_escalation: записывает событие с типом escalation и action=manual")
    async def test_33841f1a_record_escalation_writes_event(self):
        from escalation.service import record_escalation

        with autotest.step("Act: вызов record_escalation с source=manual"):
            cap = _Cap()
            await record_escalation(cap, "s1", "u1", "lab-1", source="manual")
            e = cap.added[0]
        with autotest.step("Assert: event_type и action корректны"):
            assert_equal(e.event_type, "escalation", "event_type = escalation")
            assert_equal(e.action, "manual", "action = manual")

    @autotest.num("1243")
    @autotest.external_id("4253a169-acd0-494f-b210-07482d6dea0d")
    @autotest.name(
        "record_escalation: source=objective → action=objective, success=False, severity=warn"
    )
    async def test_4253a169_record_escalation_objective_source(self):
        from escalation.service import record_escalation

        with autotest.step("Act: вызов record_escalation с source=objective"):
            cap = _Cap()
            await record_escalation(cap, "s2", "u2", "lab-2", source="objective")
            e = cap.added[0]
        with autotest.step("Assert: action, success и severity корректны"):
            assert_equal(e.action, "objective", "action = objective")
            assert_false(e.success, "success = False")
            assert_equal(e.severity, "warn", "severity = warn")
