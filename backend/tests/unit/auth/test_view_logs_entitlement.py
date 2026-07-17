import pytest
from mcp_sdk.testing import autotest
from types import SimpleNamespace

from auth.dependencies import may_view_agent_logs, can_view_session_activity

pytestmark = [pytest.mark.unit, pytest.mark.auth]

_VIEWER_ROLES = {"instructor", "admin"}


@pytest.mark.parametrize(
    "role,flag,exp",
    [
        ("student", None, False),
        ("instructor", None, True),
        ("admin", None, True),
        ("student", True, True),
        ("instructor", False, False),
    ],
)
@autotest.name("may_view_agent_logs: матрица роль/тоггл/viewer_roles")
def test_may_view_agent_logs(role, flag, exp):
    assert may_view_agent_logs(role, flag, _VIEWER_ROLES) is exp


@autotest.name("can_view_session_activity: владелец-студент с правом видит свою сессию")
def test_owner_student_sees_own_session():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "owner", "role": "student", "can_view_logs": True}
    assert can_view_session_activity(user, sess) is True


@autotest.name("can_view_session_activity: препод с правом видит чужую сессию")
def test_instructor_sees_other_session():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "x", "role": "instructor", "can_view_logs": True}
    assert can_view_session_activity(user, sess) is True


@autotest.name("can_view_session_activity: студент без права не видит")
def test_student_no_right():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "x", "role": "student", "can_view_logs": True}
    assert can_view_session_activity(user, sess) is False


@autotest.name("can_view_session_activity: can_view_logs=False блокирует")
def test_can_view_logs_false_blocks():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "owner", "role": "student", "can_view_logs": False}
    assert can_view_session_activity(user, sess) is False
