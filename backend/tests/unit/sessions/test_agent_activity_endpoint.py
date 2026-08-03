"""Tests for the agent activity history endpoint and the permission resolver."""

from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest

from auth.dependencies import can_view_session_activity

pytestmark = [pytest.mark.unit]


# ── can_view_session_activity matrix ─────────────────────────────────────────


@autotest.num("3251")
@autotest.external_id("36f5c7a1-e9f7-42ac-a682-5471c6fd22e0")
@autotest.name("can_view_session_activity: permission matrix for viewing session activity")
@pytest.mark.parametrize(
    "user,expected",
    [
        # owner with flag → True
        ({"id": "owner", "role": "student", "can_view_logs": True}, True),
        # instructor with flag → True (not the owner)
        ({"id": "x", "role": "instructor", "can_view_logs": True}, True),
        # non-owner student with flag → False
        ({"id": "x", "role": "student", "can_view_logs": True}, False),
        # owner without flag → False
        ({"id": "owner", "role": "student", "can_view_logs": False}, False),
        # flag missing entirely → False
        ({"id": "owner", "role": "instructor"}, False),
    ],
)
def test_36f5c7a1_can_view_session_activity_matrix(user, expected):
    sess = SimpleNamespace(user_id="owner")
    assert can_view_session_activity(user, sess) is expected


# ── HTTP test via direct function call ──────────────────────────────────────


class _FakeActivityLog:
    """Stub activity log with a fixed historical response."""

    def __init__(self, events):
        self._events = events

    async def history(self, session_id, since, limit):
        return self._events


@autotest.num("3252")
@autotest.external_id("8fccb0f4-c814-4166-8081-216a65cc8e1f")
@autotest.name("get_agent_activity: returns events when permission is granted")
@pytest.mark.asyncio
async def test_8fccb0f4_get_agent_activity_entitled():
    from sessions.routers.queries import get_agent_activity

    events = [SimpleNamespace(id="e1"), SimpleNamespace(id="e2")]
    activity = _FakeActivityLog(events)
    session = SimpleNamespace(user_id="u1")
    user = {"id": "u1", "role": "student", "can_view_logs": True}

    # db.get returns a fake session, patched directly via DI arguments
    class _FakeDB:
        async def get(self, model_cls, pk):
            return session

    result = await get_agent_activity(
        session_id="s1",
        since=None,
        limit=200,
        current_user=user,
        activity=activity,
        db=_FakeDB(),
    )
    assert result == events


@autotest.num("3253")
@autotest.external_id("907a6e0a-81d2-4503-84e5-e668027d1c01")
@autotest.name("get_agent_activity: 403 when permission is missing")
@pytest.mark.asyncio
async def test_907a6e0a_get_agent_activity_forbidden():
    from i18n import LocalizedError
    from sessions.routers.queries import get_agent_activity

    activity = _FakeActivityLog([])
    session = SimpleNamespace(user_id="other_user")
    user = {"id": "u1", "role": "student", "can_view_logs": True}

    class _FakeDB:
        async def get(self, model_cls, pk):
            return session

    with pytest.raises(LocalizedError) as exc_info:
        await get_agent_activity(
            session_id="s1",
            since=None,
            limit=200,
            current_user=user,
            activity=activity,
            db=_FakeDB(),
        )
    assert exc_info.value.status_code == 403


@autotest.num("3254")
@autotest.external_id("b528c845-35aa-41a8-87cb-dd05f0b419ab")
@autotest.name("get_agent_activity: 404 when the session is missing")
@pytest.mark.asyncio
async def test_b528c845_get_agent_activity_not_found():
    from i18n import LocalizedError
    from sessions.routers.queries import get_agent_activity

    activity = _FakeActivityLog([])
    user = {"id": "u1", "role": "instructor", "can_view_logs": True}

    class _FakeDB:
        async def get(self, model_cls, pk):
            return None

    with pytest.raises(LocalizedError) as exc_info:
        await get_agent_activity(
            session_id="s1",
            since=None,
            limit=200,
            current_user=user,
            activity=activity,
            db=_FakeDB(),
        )
    assert exc_info.value.status_code == 404
