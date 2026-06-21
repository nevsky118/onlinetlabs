import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from experiment.control_arm import ControlArm, assign_arm

pytestmark = [pytest.mark.unit]


class TestControlArm:
    @autotest.num("1032")
    @autotest.external_id("a929abc0-26b5-4f8b-a70c-7d84616f21bb")
    @autotest.name("ControlArm: значения enum — open и closed")
    def test_a929abc0_arm_values(self):
        with autotest.step("Act: собрать значения enum"):
            values = {a.value for a in ControlArm}
        with autotest.step("Assert: ровно open и closed"):
            assert_equal(values, {"open", "closed"}, "два плеча")

    @autotest.num("1033")
    @autotest.external_id("6e20da78-7625-4360-961b-6d07d68afcd5")
    @autotest.name("ControlArm: assign_arm возвращает OPEN при первом элементе")
    def test_6e20da78_assign_arm_valid(self, monkeypatch):
        with autotest.step("Arrange: подменить random.choice → первый элемент"):
            import experiment.control_arm as m
            monkeypatch.setattr(m.random, "choice", lambda seq: seq[0])
        with autotest.step("Act: вызвать assign_arm"):
            result = assign_arm()
        with autotest.step("Assert: результат = OPEN"):
            assert_equal(result, ControlArm.OPEN, "assign_arm вернул OPEN")
