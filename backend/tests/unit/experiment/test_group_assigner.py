import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from experiment.group_assigner import ExperimentGroup, assign_group

pytestmark = [pytest.mark.unit]


class TestGroupAssigner:
    @autotest.num("600")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-600000000001")
    @autotest.name("assign_group: возвращает control или experimental")
    def test_a1b2c3d4_assign_group_valid(self):
        with autotest.step("Назначаем группу 100 раз"):
            groups = {assign_group() for _ in range(100)}

        with autotest.step("Обе группы встречаются"):
            assert_true(ExperimentGroup.CONTROL in groups, "control встречается")
            assert_true(ExperimentGroup.EXPERIMENTAL in groups, "experimental встречается")

    @autotest.num("601")
    @autotest.external_id("b2c3d4e5-f6a7-4890-bcde-601000000002")
    @autotest.name("ExperimentGroup: значения enum")
    def test_b2c3d4e5_enum_values(self):
        with autotest.step("Проверяем значения"):
            assert_equal(ExperimentGroup.CONTROL, "control", "control")
            assert_equal(ExperimentGroup.EXPERIMENTAL, "experimental", "experimental")
