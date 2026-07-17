"""Тесты проводки observe-наблюдений П1 через ControlInterface-шов (Task 7)."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from config.config_model import LearningAnalyticsConfig
from control_interface.interface import InterfaceDenied
from learning_analytics.collector import BehavioralCollector
from mcp_sdk.models import UserAction, LogLevel

pytestmark = [pytest.mark.unit]

_SESSION_ID = "sess-t7-001"
_USER_ID = "user-t7-001"
_LAB_SLUG = "lan-static-ip"

_ACTION = UserAction(
    timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    component_id="node-1",
    action="start_node",
    raw_command=None,
    success=True,
)


def _make_cfg():
    return LearningAnalyticsConfig(
        poll_interval=60,
        mcp_actions_limit=10,
        mcp_logs_limit=10,
        dedup_max_size=100,
    )


def _make_collector(control_interface):
    mcp = MagicMock()
    db_factory = MagicMock()
    col = BehavioralCollector(mcp, db_factory, _make_cfg(), control_interface=control_interface)
    col._session_id = _SESSION_ID
    col._user_id = _USER_ID
    col._lab_slug = _LAB_SLUG
    col._ctx = object()
    return col


class TestCollectorSeam:
    @autotest.num("1790")
    @autotest.external_id("d08a21cd-84b2-4989-9a90-603b803e2bf8")
    @autotest.name("collector: observe идёт через шов (ControlInterface.observe вызван)")
    @pytest.mark.asyncio
    async def test_d08a21cd_observe_routed_through_seam(self):
        with autotest.step("Arrange: ControlInterface.observe возвращает список действий"):
            ci = MagicMock()
            ci.observe = AsyncMock(return_value=[_ACTION])
            col = _make_collector(ci)

        with autotest.step("Act: _fetch_actions"):
            result = await col._fetch_actions()

        with autotest.step("Assert: observe вызван с правильными аргументами, mcp не трогался"):
            ci.observe.assert_awaited_once()
            call_kwargs = ci.observe.await_args
            assert_equal(call_kwargs.args[0], "list_user_actions", "tool")
            assert_equal(call_kwargs.kwargs["user_id"], _USER_ID, "user_id")
            assert_equal(call_kwargs.kwargs["session_id"], _SESSION_ID, "session_id")
            assert_equal(call_kwargs.kwargs["lab_slug"], _LAB_SLUG, "lab_slug")
            col._mcp.list_user_actions.assert_not_called()
            assert_equal(len(result), 1, "одно событие")

    @autotest.num("1791")
    @autotest.external_id("8f755f33-ea16-49f6-b3da-fa7683d62a04")
    @autotest.name("collector: InterfaceDenied(consent) → наблюдение пропускается, нет краша")
    @pytest.mark.asyncio
    async def test_8f755f33_denied_consent_skips_without_crash(self):
        with autotest.step("Arrange: observe выбрасывает InterfaceDenied(consent)"):
            ci = MagicMock()
            ci.observe = AsyncMock(side_effect=InterfaceDenied("consent"))
            col = _make_collector(ci)

        with autotest.step("Act: _fetch_actions — не должно упасть"):
            result = await col._fetch_actions()

        with autotest.step("Assert: пустой список, mcp не трогался"):
            assert_equal(result, [], "пустой при отказе")
            col._mcp.list_user_actions.assert_not_called()

    @autotest.num("1792")
    @autotest.external_id("3621d315-3606-4638-9a11-d3c06bb03bfb")
    @autotest.name("collector: без шва (None) → fallback на mcp_client напрямую")
    @pytest.mark.asyncio
    async def test_3621d315_no_seam_fallback_to_mcp(self):
        with autotest.step(
            "Arrange: control_interface=None, mcp.list_user_actions возвращает список"
        ):
            col = _make_collector(None)
            col._mcp.list_user_actions = AsyncMock(return_value=[_ACTION])

        with autotest.step("Act: _fetch_actions"):
            result = await col._fetch_actions()

        with autotest.step("Assert: mcp.list_user_actions вызван, событие возвращено"):
            col._mcp.list_user_actions.assert_awaited_once()
            assert_equal(len(result), 1, "одно событие через fallback")

    @autotest.num("1793")
    @autotest.external_id("7d41615e-37c2-4f82-8f3c-82bf3bbeaafe")
    @autotest.name("collector: InterfaceDenied(isolation) в get_logs → пропуск без краша")
    @pytest.mark.asyncio
    async def test_7d41615e_denied_isolation_logs_skips(self):
        with autotest.step("Arrange: observe выбрасывает InterfaceDenied(isolation) на get_logs"):
            ci = MagicMock()
            ci.observe = AsyncMock(side_effect=InterfaceDenied("isolation"))
            col = _make_collector(ci)

        with autotest.step("Act: _fetch_logs — не должно упасть"):
            result = await col._fetch_logs()

        with autotest.step("Assert: пустой список"):
            assert_equal(result, [], "пустой при изоляции")
