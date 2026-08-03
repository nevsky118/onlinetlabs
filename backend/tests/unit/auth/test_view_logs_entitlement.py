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
@autotest.num("3217")
@autotest.external_id("f665a33c-a739-4e5a-b4c6-1482d66b4646")
@autotest.name("may_view_agent_logs: role/flag/viewer_roles matrix")
def test_f665a33c_may_view_agent_logs(role, flag, exp):
    assert may_view_agent_logs(role, flag, _VIEWER_ROLES) is exp


@autotest.num("3218")
@autotest.external_id("5cab5838-9f00-40e8-a2a1-81ce134f17af")
@autotest.name("can_view_session_activity: owner student with the flag sees their own session")
def test_5cab5838_owner_student_sees_own_session():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "owner", "role": "student", "can_view_logs": True}
    assert can_view_session_activity(user, sess) is True


@autotest.num("3219")
@autotest.external_id("e1ffb63d-3972-4829-94fd-b883155a2240")
@autotest.name("can_view_session_activity: instructor with the flag sees someone else's session")
def test_e1ffb63d_instructor_sees_other_session():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "x", "role": "instructor", "can_view_logs": True}
    assert can_view_session_activity(user, sess) is True


@autotest.num("3220")
@autotest.external_id("9a9f1714-30ed-4fd3-b545-0168e4fea1b1")
@autotest.name("can_view_session_activity: student without the flag does not see it")
def test_9a9f1714_student_no_right():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "x", "role": "student", "can_view_logs": True}
    assert can_view_session_activity(user, sess) is False


@autotest.num("3221")
@autotest.external_id("74ab32c6-99e2-43f2-b57b-e8a17b777ed6")
@autotest.name("can_view_session_activity: can_view_logs=False blocks it")
def test_74ab32c6_can_view_logs_false_blocks():
    sess = SimpleNamespace(user_id="owner")
    user = {"id": "owner", "role": "student", "can_view_logs": False}
    assert can_view_session_activity(user, sess) is False
