import pytest
from mcp_sdk.testing import autotest

from auth.dependencies import may_select_model

pytestmark = [pytest.mark.unit, pytest.mark.auth]


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
def test_11f5e1a1_may_select_model(role, toggle, expected):
    roles = {"student", "instructor", "admin"}
    assert may_select_model(role, toggle, roles) is expected


@autotest.num("3214")
@autotest.external_id("6a2c9219-e5ca-4199-ba7b-c697a0abcbfa")
@autotest.name("may_select_model: role not in selectable_roles and toggle None → False")
def test_6a2c9219_may_select_model_role_not_in_selectable_roles():
    """Role NOT in selectable_roles, toggle None → False."""
    assert may_select_model("student", None, {"instructor", "admin"}) is False
