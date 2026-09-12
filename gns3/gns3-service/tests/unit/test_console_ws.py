"""Tests console proxy session resolution and relay teardown."""

import asyncio
import logging

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from src.db.models import SessionStatus
from src.routers.console_ws import _make_tap, _resolve_session
from tests.settings.data.console_data import (
    ConsoleStalledLookupData,
    ConsoleWsSessionScenarioData,
    StalledConsoleProxyData,
)

pytestmark = [pytest.mark.unit]


class TestResolveSession:
    @autotest.num("3554")
    @autotest.external_id("64bb09f5-d5b8-4aaa-948c-350cc298e22d")
    @autotest.name(
        "_resolve_session: the active session wins over a closed one for the same project"
    )
    async def test_64bb09f5_the_active_session_wins_over_a_closed_one(self):
        with autotest.step("Arrange: one project with a closed and an active session"):
            app, active_id = await ConsoleWsSessionScenarioData.build(
                "proj-1", SessionStatus.CLOSED
            )

        with autotest.step("Act: resolve the project"):
            resolved = await _resolve_session(app, "proj-1")

        with autotest.step("Assert: the active session is chosen"):
            assert_equal(resolved, active_id, "active session")

    @autotest.num("3555")
    @autotest.external_id("7532a4a0-18ae-4d54-91e4-59246569a045")
    @autotest.name(
        "_resolve_session: the newer non-closed session wins over an older one, both live"
    )
    async def test_7532a4a0_the_newer_non_closed_session_wins_over_an_older_one(self):
        with autotest.step("Arrange: one project with two active sessions, different ages"):
            app, newer_id = await ConsoleWsSessionScenarioData.build("proj-2", SessionStatus.ACTIVE)

        with autotest.step("Act: resolve the project"):
            resolved = await _resolve_session(app, "proj-2")

        with autotest.step("Assert: the newer session is chosen"):
            assert_equal(resolved, newer_id, "newer session")

    @autotest.num("3556")
    @autotest.external_id("67d1d9bd-c1c4-4e31-9443-451fc4d86de5")
    @autotest.name("_resolve_session: two non-closed sessions sharing a project logs a warning")
    async def test_67d1d9bd_ambiguous_project_logs_a_warning(self, caplog):
        with autotest.step("Arrange: one project with two active sessions, different ages"):
            app, newer_id = await ConsoleWsSessionScenarioData.build("proj-2", SessionStatus.ACTIVE)

        with autotest.step("Act: resolve the project"):
            with caplog.at_level(logging.WARNING, logger="src.routers.console_ws"):
                resolved = await _resolve_session(app, "proj-2")

        with autotest.step("Assert: a warning was logged and the newer session was still used"):
            assert_equal(resolved, newer_id, "newer session used despite the ambiguity")
            assert_true(
                any("proj-2" in record.message for record in caplog.records),
                "warning names the ambiguous project",
            )


class TestRelayTeardown:
    @autotest.num("3557")
    @autotest.external_id("498d4ea2-3628-447f-8fde-6b1606e4371a")
    @autotest.name("console_ws: cancelling the handler stops both relay pumps")
    async def test_498d4ea2_cancelling_the_handler_stops_both_pumps(self, monkeypatch):
        with autotest.step("Arrange: a proxy over two never-ending fake sockets"):
            handler, client, upstream = StalledConsoleProxyData.build(monkeypatch)
            task = asyncio.create_task(handler)
            await asyncio.sleep(0)

        with autotest.step("Act: cancel the handler"):
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        with autotest.step("Assert: both relay pumps were cancelled"):
            assert_true(client.cancelled, "client-to-upstream pump cancelled")
            assert_true(upstream.cancelled, "upstream-to-client pump cancelled")

        with autotest.step("Assert: both sockets were closed"):
            assert_true(client.closed, "client closed")
            assert_true(upstream.closed, "upstream closed")


class TestSessionLookupTimeout:
    """A slow session lookup does not delay the console handshake."""

    @autotest.num("3573")
    @autotest.external_id("5f5434d4-26a5-4dc3-b478-b6c951831a05")
    @autotest.name("_make_tap: a session lookup that never answers gives up without a tap")
    async def test_5f5434d4_session_lookup_timeout_gives_up_without_a_tap(
        self, monkeypatch, caplog
    ):
        with autotest.step("Arrange: a socket whose session lookup hangs"):
            websocket = ConsoleStalledLookupData.build(monkeypatch, timeout_sec=0.05)

        with autotest.step("Act: build the tap, refusing to wait longer than the handshake"):
            with caplog.at_level(logging.WARNING, logger="src.routers.console_ws"):
                tap = await asyncio.wait_for(_make_tap(websocket, "proj-1", "node-1"), 2.0)

        with autotest.step("Assert: no tap, and the give-up is logged"):
            assert_true(tap is None, "capture off")
            assert_true(
                any("timed out" in record.message for record in caplog.records),
                "the timeout is logged",
            )
