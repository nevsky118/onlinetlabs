"""Tests for ControlInterface: 5 denial branches + 2 happy paths."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from control_interface.interface import ControlInterface, InterfaceDenied
from experiment.assignment import ControlArm

pytestmark = [pytest.mark.unit]

_TOOL_OBS = "list_user_actions"
_TOOL_ACT = "execute_action"
_USER = "user-11111111"
_SESSION = "sess-22222222"


def _make_mcp():
    mcp = MagicMock()
    mcp._call_tool = AsyncMock(return_value={"data": "ok"})
    mcp.execute_action = AsyncMock(return_value={"done": True})
    # observe dispatches through a typed wrapper (ctx injection + serialization).
    mcp.list_user_actions = AsyncMock(return_value={"data": "ok"})
    return mcp


def _make_config(cooldown: float = 60.0):
    cfg = MagicMock()
    cfg.cooldown_period = cooldown
    return cfg


def _make_db_factory(owned=True, consent=True):
    """Fake db_factory: async ctx manager, returns a stub db."""
    db = MagicMock()

    @asynccontextmanager
    async def factory():
        yield db

    return factory, db


class TestControlInterface:
    # ── observe happy path ────────────────────────────────────────────────

    @autotest.num("1770")
    @autotest.external_id("8d4e6106-a42a-42a4-ac83-587b9ca6830f")
    @autotest.name("observe: classify+consent+owner → _call_tool вызван, audit(success=True)")
    async def test_8d4e6106_observe_happy(self):
        mcp = _make_mcp()
        factory, db = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with (
            patch(
                "control_interface.interface.get_owned_session",
                new=AsyncMock(return_value=object()),
            ),
            patch("control_interface.interface.has_consent", new=AsyncMock(return_value=True)),
            patch("control_interface.interface.record", new=AsyncMock()) as mock_record,
        ):
            result = await iface.observe(
                _TOOL_OBS, ctx=None, arguments={}, user_id=_USER, session_id=_SESSION
            )

        with autotest.step("Assert: типизированная обёртка вызвана с ctx"):
            mcp.list_user_actions.assert_awaited_once_with(None)
        with autotest.step("Assert: audit записан с success=True"):
            assert_true(mock_record.called, "record вызван")
            call_kwargs = mock_record.call_args.kwargs
            assert_equal(call_kwargs["success"], True, "success")
            assert_equal(call_kwargs["kind"], "observe", "kind")

    # ── act happy path + rate-backstop ───────────────────────────────────

    @autotest.num("1771")
    @autotest.external_id("c21fc83a-4d93-4c05-bfcc-667a29b2e159")
    @autotest.name("act: первый вызов → execute_action; второй < cooldown → rate-denied")
    async def test_c21fc83a_act_then_rate(self):
        mcp = _make_mcp()
        factory, db = _make_db_factory()
        cfg = _make_config(cooldown=60.0)
        iface = ControlInterface(mcp, factory, cfg)

        with (
            patch(
                "control_interface.interface.get_owned_session",
                new=AsyncMock(return_value=object()),
            ),
            patch("control_interface.interface.has_consent", new=AsyncMock(return_value=True)),
            patch("control_interface.interface.record", new=AsyncMock()),
        ):
            # first call succeeds
            await iface.act(
                _TOOL_ACT,
                ctx=None,
                arguments={"action_name": "start_node", "params": {}},
                user_id=_USER,
                session_id=_SESSION,
                arm=ControlArm.CLOSED,
            )

        with autotest.step("Assert: execute_action вызван первый раз"):
            mcp.execute_action.assert_awaited_once()

        # second call immediately should fail with rate limit
        with (
            patch(
                "control_interface.interface.get_owned_session",
                new=AsyncMock(return_value=object()),
            ),
            patch("control_interface.interface.has_consent", new=AsyncMock(return_value=True)),
            patch("control_interface.interface.record", new=AsyncMock()),
        ):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.act(
                    _TOOL_ACT,
                    ctx=None,
                    arguments={"action_name": "start_node", "params": {}},
                    user_id=_USER,
                    session_id=_SESSION,
                    arm=ControlArm.CLOSED,
                )

        with autotest.step("Assert: причина rate"):
            assert_equal(exc_info.value.reason, "rate", "reason")

    # ── act in open arm → open_arm ────────────────────────────────────────

    @autotest.num("1772")
    @autotest.external_id("e896a19f-9527-4485-8534-fb6bc2de6ece")
    @autotest.name("act в OPEN плече → InterfaceDenied(open_arm), execute_action не вызван")
    async def test_e896a19f_act_open_arm(self):
        mcp = _make_mcp()
        factory, db = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with (
            patch(
                "control_interface.interface.get_owned_session",
                new=AsyncMock(return_value=object()),
            ),
            patch("control_interface.interface.has_consent", new=AsyncMock(return_value=True)),
            patch("control_interface.interface.record", new=AsyncMock()),
        ):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.act(
                    _TOOL_ACT,
                    ctx=None,
                    arguments={},
                    user_id=_USER,
                    session_id=_SESSION,
                    arm=ControlArm.OPEN,
                )

        with autotest.step("Assert: reason=open_arm, execute_action не тронут"):
            assert_equal(exc_info.value.reason, "open_arm", "reason")
            mcp.execute_action.assert_not_awaited()

    # ── unclassified tool → unclassified ──────────────────────────────────

    @autotest.num("1773")
    @autotest.external_id("3f314b4d-7ba2-4615-9889-24a00f12e5e8")
    @autotest.name("observe: неклассифицированный tool → InterfaceDenied(unclassified)")
    async def test_3f314b4d_unclassified(self):
        mcp = _make_mcp()
        factory, _ = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with patch("control_interface.interface.record", new=AsyncMock()):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.observe(
                    "rm_rf_all", ctx=None, arguments={}, user_id=_USER, session_id=_SESSION
                )

        with autotest.step("Assert: reason=unclassified"):
            assert_equal(exc_info.value.reason, "unclassified", "reason")

    # ── foreign session → isolation ───────────────────────────────────────

    @autotest.num("1774")
    @autotest.external_id("aa9acc55-89a8-4137-9094-2d6ab2c34102")
    @autotest.name("observe: чужая сессия (get_owned_session→None) → InterfaceDenied(isolation)")
    async def test_aa9acc55_isolation(self):
        mcp = _make_mcp()
        factory, _ = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with (
            patch(
                "control_interface.interface.get_owned_session", new=AsyncMock(return_value=None)
            ),
            patch("control_interface.interface.record", new=AsyncMock()),
        ):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.observe(
                    _TOOL_OBS, ctx=None, arguments={}, user_id=_USER, session_id=_SESSION
                )

        with autotest.step("Assert: reason=isolation"):
            assert_equal(exc_info.value.reason, "isolation", "reason")

    # ── act: no consent → consent ─────────────────────────────────────────

    @autotest.num("1775")
    @autotest.external_id("881af810-b603-4689-b511-e03c76db5616")
    @autotest.name("act: нет согласия → InterfaceDenied(consent)")
    async def test_881af810_no_consent(self):
        mcp = _make_mcp()
        factory, _ = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with (
            patch(
                "control_interface.interface.get_owned_session",
                new=AsyncMock(return_value=object()),
            ),
            patch("control_interface.interface.has_consent", new=AsyncMock(return_value=False)),
            patch("control_interface.interface.record", new=AsyncMock()),
        ):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.act(
                    _TOOL_ACT,
                    ctx=None,
                    arguments={},
                    user_id=_USER,
                    session_id=_SESSION,
                    arm=ControlArm.CLOSED,
                )

        with autotest.step("Assert: reason=consent"):
            assert_equal(exc_info.value.reason, "consent", "reason")

    # ── observe: no consent → consent ─────────────────────────────────────

    @autotest.num("1776")
    @autotest.external_id("507643b8-80b1-4f98-b42a-a1b346faade5")
    @autotest.name("observe: нет согласия → InterfaceDenied(consent)")
    async def test_507643b8_observe_no_consent(self):
        mcp = _make_mcp()
        factory, _ = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with (
            patch(
                "control_interface.interface.get_owned_session",
                new=AsyncMock(return_value=object()),
            ),
            patch("control_interface.interface.has_consent", new=AsyncMock(return_value=False)),
            patch("control_interface.interface.record", new=AsyncMock()),
        ):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.observe(
                    _TOOL_OBS, ctx=None, arguments={}, user_id=_USER, session_id=_SESSION
                )

        with autotest.step("Assert: reason=consent"):
            assert_equal(exc_info.value.reason, "consent", "reason")
