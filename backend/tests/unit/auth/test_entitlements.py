import pytest
from mcp_sdk.testing import autotest

from auth.dependencies import may_select_model

pytestmark = [pytest.mark.unit, pytest.mark.auth]


@pytest.mark.parametrize("role,toggle,expected", [
    ("student", None, True),       # пермиссивный дефолт: роль в selectable_roles
    ("student", False, False),     # точечный дизейбл перебивает роль
    ("instructor", None, True),
    ("student", True, True),       # явный тоггл включён — даёт доступ
])
@autotest.name("may_select_model: матрица роль/тоггл/selectable_roles")
def test_may_select_model(role, toggle, expected):
    roles = {"student", "instructor", "admin"}
    assert may_select_model(role, toggle, roles) is expected


@autotest.name("may_select_model: роль не в selectable_roles и toggle None → False")
def test_may_select_model_role_not_in_selectable_roles():
    """Роль НЕ в selectable_roles, toggle None → False."""
    assert may_select_model("student", None, {"instructor", "admin"}) is False
