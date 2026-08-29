import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from auth.dependencies import may_select_model

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestEntitlements:
    @pytest.mark.parametrize(
        "role,toggle,expected",
        [
            ("student", None, True),  # permissive default: role is in selectable_roles
            ("student", False, False),  # targeted disable overrides role
            ("instructor", None, True),
            ("student", True, True),  # explicit toggle enabled grants access
        ],
    )
    @autotest.num("3213")
    @autotest.external_id("11f5e1a1-d90a-409b-9f87-99303790cffa")
    @autotest.name("may_select_model: role/toggle/selectable_roles matrix")
    def test_11f5e1a1_may_select_model(self, role, toggle, expected):
        with autotest.step("Arrange: selectable_roles"):
            roles = {"student", "instructor", "admin"}

        with autotest.step("Act+Assert: may_select_model matches the expected verdict"):
            assert_equal(may_select_model(role, toggle, roles), expected, "verdict")

    @autotest.num("3214")
    @autotest.external_id("6a2c9219-e5ca-4199-ba7b-c697a0abcbfa")
    @autotest.name("may_select_model: role not in selectable_roles and toggle None → False")
    def test_6a2c9219_may_select_model_role_not_in_selectable_roles(self):
        """Role NOT in selectable_roles, toggle None → False."""
        with autotest.step("Act+Assert: role outside selectable_roles with toggle None → False"):
            assert_equal(
                may_select_model("student", None, {"instructor", "admin"}),
                False,
                "may select model",
            )
