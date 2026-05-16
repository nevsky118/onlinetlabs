import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from experiment.group_assigner import ExperimentGroup, assign_group

pytestmark = [pytest.mark.unit]


class TestGroupAssigner:
    @autotest.num("600")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-600000000001")
    @autotest.name("assign_group: возвращает group_a или group_b")
    def test_a1b2c3d4_assign_group_valid(self):
        # Arrange
        with autotest.step("Готовим количество назначений"):
            iterations = 100

        # Act
        with autotest.step("Назначаем группу 100 раз"):
            groups = {assign_group() for _ in range(iterations)}

        # Assert
        with autotest.step("Обе группы встречаются"):
            assert_true(ExperimentGroup.GROUP_A in groups, "group_a встречается")
            assert_true(ExperimentGroup.GROUP_B in groups, "group_b встречается")

    @autotest.num("601")
    @autotest.external_id("b2c3d4e5-f6a7-4890-bcde-601000000002")
    @autotest.name("ExperimentGroup: значения enum")
    def test_b2c3d4e5_enum_values(self):
        # Arrange
        with autotest.step("Готовим ожидаемые значения групп"):
            expected_group_a = "group_a"
            expected_group_b = "group_b"

        # Act
        with autotest.step("Читаем значения enum"):
            group_a = ExperimentGroup.GROUP_A
            group_b = ExperimentGroup.GROUP_B

        # Assert
        with autotest.step("Проверяем значения"):
            assert_equal(group_a, expected_group_a, "group_a")
            assert_equal(group_b, expected_group_b, "group_b")
