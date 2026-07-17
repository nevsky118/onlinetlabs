"""Тесты ControlInterface: 5 ветвей отказа + 2 happy path."""
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
    # observe диспатчит через типизированную обёртку (инъекция ctx + сериализация).
    mcp.list_user_actions = AsyncMock(return_value={"data": "ok"})
    return mcp


def _make_config(cooldown: float = 60.0):
    cfg = MagicMock()
    cfg.cooldown_period = cooldown
    return cfg


def _make_db_factory(owned=True, consent=True):
    """Фейковый db_factory: async ctx manager, возвращает фиктивный db."""
    db = MagicMock()

    @asynccontextmanager
    async def factory():
        yield db

    return factory, db


class TestControlInterface:
    # ── observe happy path ────────────────────────────────────────────────

    @autotest.num("1770")
    @autotest.external_id("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    @autotest.name("observe: classify+consent+owner → _call_tool вызван, audit(success=True)")
    async def test_a1b2c3d4_observe_happy(self):
        mcp = _make_mcp()
        factory, db = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with patch("control_interface.interface.get_owned_session", new=AsyncMock(return_value=object())), \
             patch("control_interface.interface.has_consent", new=AsyncMock(return_value=True)), \
             patch("control_interface.interface.record", new=AsyncMock()) as mock_record:
            result = await iface.observe(_TOOL_OBS, ctx=None, arguments={},
                                         user_id=_USER, session_id=_SESSION)

        with autotest.step("Assert: типизированная обёртка вызвана с ctx"):
            mcp.list_user_actions.assert_awaited_once_with(None)
        with autotest.step("Assert: audit записан с success=True"):
            assert_true(mock_record.called, "record вызван")
            call_kwargs = mock_record.call_args.kwargs
            assert_equal(call_kwargs["success"], True, "success")
            assert_equal(call_kwargs["kind"], "observe", "kind")

    # ── act happy path + rate-backstop ───────────────────────────────────

    @autotest.num("1771")
    @autotest.external_id("b2c3d4e5-f6a7-8901-bcde-f12345678901")
    @autotest.name("act: первый вызов → execute_action; второй < cooldown → rate-denied")
    async def test_b2c3d4e5_act_then_rate(self):
        mcp = _make_mcp()
        factory, db = _make_db_factory()
        cfg = _make_config(cooldown=60.0)
        iface = ControlInterface(mcp, factory, cfg)

        with patch("control_interface.interface.get_owned_session", new=AsyncMock(return_value=object())), \
             patch("control_interface.interface.has_consent", new=AsyncMock(return_value=True)), \
             patch("control_interface.interface.record", new=AsyncMock()):
            # первый вызов — успех
            await iface.act(_TOOL_ACT, ctx=None,
                            arguments={"action_name": "start_node", "params": {}},
                            user_id=_USER, session_id=_SESSION, arm=ControlArm.CLOSED)

        with autotest.step("Assert: execute_action вызван первый раз"):
            mcp.execute_action.assert_awaited_once()

        # второй вызов немедленно — должен упасть с rate
        with patch("control_interface.interface.get_owned_session", new=AsyncMock(return_value=object())), \
             patch("control_interface.interface.has_consent", new=AsyncMock(return_value=True)), \
             patch("control_interface.interface.record", new=AsyncMock()):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.act(_TOOL_ACT, ctx=None,
                                arguments={"action_name": "start_node", "params": {}},
                                user_id=_USER, session_id=_SESSION, arm=ControlArm.CLOSED)

        with autotest.step("Assert: причина rate"):
            assert_equal(exc_info.value.reason, "rate", "reason")

    # ── act в open-плече → open_arm ───────────────────────────────────────

    @autotest.num("1772")
    @autotest.external_id("c3d4e5f6-a7b8-9012-cdef-123456789012")
    @autotest.name("act в OPEN плече → InterfaceDenied(open_arm), execute_action не вызван")
    async def test_c3d4e5f6_act_open_arm(self):
        mcp = _make_mcp()
        factory, db = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with patch("control_interface.interface.get_owned_session", new=AsyncMock(return_value=object())), \
             patch("control_interface.interface.has_consent", new=AsyncMock(return_value=True)), \
             patch("control_interface.interface.record", new=AsyncMock()):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.act(_TOOL_ACT, ctx=None, arguments={},
                                user_id=_USER, session_id=_SESSION, arm=ControlArm.OPEN)

        with autotest.step("Assert: reason=open_arm, execute_action не тронут"):
            assert_equal(exc_info.value.reason, "open_arm", "reason")
            mcp.execute_action.assert_not_awaited()

    # ── неклассифицированный tool → unclassified ─────────────────────────

    @autotest.num("1773")
    @autotest.external_id("d4e5f6a7-b8c9-0123-defa-234567890123")
    @autotest.name("observe: неклассифицированный tool → InterfaceDenied(unclassified)")
    async def test_d4e5f6a7_unclassified(self):
        mcp = _make_mcp()
        factory, _ = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with patch("control_interface.interface.record", new=AsyncMock()):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.observe("rm_rf_all", ctx=None, arguments={},
                                    user_id=_USER, session_id=_SESSION)

        with autotest.step("Assert: reason=unclassified"):
            assert_equal(exc_info.value.reason, "unclassified", "reason")

    # ── чужая сессия → isolation ──────────────────────────────────────────

    @autotest.num("1774")
    @autotest.external_id("e5f6a7b8-c9d0-1234-efab-345678901234")
    @autotest.name("observe: чужая сессия (get_owned_session→None) → InterfaceDenied(isolation)")
    async def test_e5f6a7b8_isolation(self):
        mcp = _make_mcp()
        factory, _ = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with patch("control_interface.interface.get_owned_session", new=AsyncMock(return_value=None)), \
             patch("control_interface.interface.record", new=AsyncMock()):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.observe(_TOOL_OBS, ctx=None, arguments={},
                                    user_id=_USER, session_id=_SESSION)

        with autotest.step("Assert: reason=isolation"):
            assert_equal(exc_info.value.reason, "isolation", "reason")

    # ── act: нет согласия → consent ───────────────────────────────────────

    @autotest.num("1775")
    @autotest.external_id("f6a7b8c9-d0e1-2345-fabc-456789012345")
    @autotest.name("act: нет согласия → InterfaceDenied(consent)")
    async def test_f6a7b8c9_no_consent(self):
        mcp = _make_mcp()
        factory, _ = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with patch("control_interface.interface.get_owned_session", new=AsyncMock(return_value=object())), \
             patch("control_interface.interface.has_consent", new=AsyncMock(return_value=False)), \
             patch("control_interface.interface.record", new=AsyncMock()):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.act(_TOOL_ACT, ctx=None, arguments={},
                                user_id=_USER, session_id=_SESSION, arm=ControlArm.CLOSED)

        with autotest.step("Assert: reason=consent"):
            assert_equal(exc_info.value.reason, "consent", "reason")

    # ── observe: нет согласия → consent ──────────────────────────────────

    @autotest.num("1776")
    @autotest.external_id("a7b8c9d0-e1f2-3456-abcd-567890123456")
    @autotest.name("observe: нет согласия → InterfaceDenied(consent)")
    async def test_a7b8c9d0_observe_no_consent(self):
        mcp = _make_mcp()
        factory, _ = _make_db_factory()
        iface = ControlInterface(mcp, factory, _make_config())

        with patch("control_interface.interface.get_owned_session", new=AsyncMock(return_value=object())), \
             patch("control_interface.interface.has_consent", new=AsyncMock(return_value=False)), \
             patch("control_interface.interface.record", new=AsyncMock()):
            with pytest.raises(InterfaceDenied) as exc_info:
                await iface.observe(_TOOL_OBS, ctx=None, arguments={},
                                    user_id=_USER, session_id=_SESSION)

        with autotest.step("Assert: reason=consent"):
            assert_equal(exc_info.value.reason, "consent", "reason")
