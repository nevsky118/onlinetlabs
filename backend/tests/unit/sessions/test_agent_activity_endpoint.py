"""Тесты эндпоинта истории активности агентов и резолвера прав."""

from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest

from auth.dependencies import can_view_session_activity

pytestmark = [pytest.mark.unit]


# ── Матрица can_view_session_activity ─────────────────────────────────────────


@autotest.name("can_view_session_activity: матрица прав на просмотр активности сессии")
@pytest.mark.parametrize(
    "user,expected",
    [
        # владелец со флагом → True
        ({"id": "owner", "role": "student", "can_view_logs": True}, True),
        # препод со флагом → True (не владелец)
        ({"id": "x", "role": "instructor", "can_view_logs": True}, True),
        # студент-не-владелец со флагом → False
        ({"id": "x", "role": "student", "can_view_logs": True}, False),
        # владелец без флага → False
        ({"id": "owner", "role": "student", "can_view_logs": False}, False),
        # флаг отсутствует вовсе → False
        ({"id": "owner", "role": "instructor"}, False),
    ],
)
def test_can_view_session_activity_matrix(user, expected):
    sess = SimpleNamespace(user_id="owner")
    assert can_view_session_activity(user, sess) is expected


# ── HTTP-тест через прямой вызов функции ──────────────────────────────────────


class _FakeActivityLog:
    """Stub-лог активности с фиксированным историческим ответом."""

    def __init__(self, events):
        self._events = events

    async def history(self, session_id, since, limit):
        return self._events


@autotest.name("get_agent_activity: возвращает события при наличии прав")
@pytest.mark.asyncio
async def test_get_agent_activity_entitled():
    from sessions.routers.queries import get_agent_activity

    events = [SimpleNamespace(id="e1"), SimpleNamespace(id="e2")]
    activity = _FakeActivityLog(events)
    session = SimpleNamespace(user_id="u1")
    user = {"id": "u1", "role": "student", "can_view_logs": True}

    # db.get возвращает фейковую сессию — патчим через DI-аргументы напрямую
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


@autotest.name("get_agent_activity: 403 при отсутствии прав")
@pytest.mark.asyncio
async def test_get_agent_activity_forbidden():
    from fastapi import HTTPException

    from sessions.routers.queries import get_agent_activity

    activity = _FakeActivityLog([])
    session = SimpleNamespace(user_id="other_user")
    user = {"id": "u1", "role": "student", "can_view_logs": True}

    class _FakeDB:
        async def get(self, model_cls, pk):
            return session

    with pytest.raises(HTTPException) as exc_info:
        await get_agent_activity(
            session_id="s1",
            since=None,
            limit=200,
            current_user=user,
            activity=activity,
            db=_FakeDB(),
        )
    assert exc_info.value.status_code == 403


@autotest.name("get_agent_activity: 404 при отсутствии сессии")
@pytest.mark.asyncio
async def test_get_agent_activity_not_found():
    from fastapi import HTTPException

    from sessions.routers.queries import get_agent_activity

    activity = _FakeActivityLog([])
    user = {"id": "u1", "role": "instructor", "can_view_logs": True}

    class _FakeDB:
        async def get(self, model_cls, pk):
            return None

    with pytest.raises(HTTPException) as exc_info:
        await get_agent_activity(
            session_id="s1",
            since=None,
            limit=200,
            current_user=user,
            activity=activity,
            db=_FakeDB(),
        )
    assert exc_info.value.status_code == 404
