from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest

from auth.dependencies import can_view_session_activity, may_view_agent_logs

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
@autotest.name("may_view_agent_logs: role/flag/viewer_roles matrix")
def test_may_view_agent_logs(role, flag, exp):
    assert may_view_agent_logs(role, flag, _VIEWER_ROLES) is exp


@autotest.name("can_view_session_activity: owner student with the flag sees their own session")
def test_owner_student_sees_own_session():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "owner", "role": "student", "can_view_logs": True}
    assert can_view_session_activity(user, sess) is True


@autotest.name("can_view_session_activity: instructor with the flag sees someone else's session")
def test_instructor_sees_other_session():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "x", "role": "instructor", "can_view_logs": True}
    assert can_view_session_activity(user, sess) is True


@autotest.name("can_view_session_activity: student without the flag does not see it")
def test_student_no_right():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "x", "role": "student", "can_view_logs": True}
    assert can_view_session_activity(user, sess) is False


@autotest.name("can_view_session_activity: can_view_logs=False blocks it")
def test_can_view_logs_false_blocks():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "owner", "role": "student", "can_view_logs": False}
    assert can_view_session_activity(user, sess) is False
