import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from experiment.assignment import ExperimentGroup, assign_group

pytestmark = [pytest.mark.unit]


class TestGroupAssigner:
    @pytest.mark.parametrize(
        "forced_group",
        [
            ExperimentGroup.GROUP_A,
            ExperimentGroup.GROUP_B,
        ],
    )
    @autotest.num("600")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-600000000001")
    @autotest.name("assign_group: возвращает обе валидные группы")
    def test_a1b2c3d4_assign_group_returns_forced_choice(self, monkeypatch, forced_group):
        # Arrange
        with autotest.step("Подменяем random.choice на детерминированную лямбду"):
            monkeypatch.setattr(
                "experiment.assignment.random.choice",
                lambda choices: forced_group,
            )

        # Act
        with autotest.step("Вызываем assign_group"):
            result = assign_group()

        # Assert
        with autotest.step("Возвращается ожидаемая группа"):
            assert_equal(result, forced_group, "assign_group вернул подменённое значение")

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
