"""Tests for the observer registry in WebSocketGateway."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_false, assert_in

from sessions.ws.gateway import WebSocketGateway

pytestmark = [pytest.mark.unit]


class TestGatewayObservers:
    @autotest.num("3255")
    @autotest.external_id("407ff2b0-076b-4652-a4db-0cbdf683e02a")
    @autotest.name("WebSocketGateway: observer is added to and removed from the registry")
    def test_407ff2b0_observer_registry(self):
        """Observer is added to/removed from the registry."""
        with autotest.step("Arrange: a gateway and an observer"):
            gw = WebSocketGateway()
            ws = object()

        with autotest.step("Act: connect_observer"):
            gw.connect_observer("s1", ws)

        with autotest.step("Assert: observer is registered"):
            assert_in(ws, gw.observers("s1"), "ws")

        with autotest.step("Act: disconnect_observer"):
            gw.disconnect_observer("s1", ws)

        with autotest.step("Assert: observer is removed"):
            assert_false(ws in gw.observers("s1"), "ws absent")

    @autotest.num("3256")
    @autotest.external_id("6732c1ce-eb4c-4bbd-a4e4-330df6fb81ee")
    @autotest.name("WebSocketGateway.observers: returns an empty set for an unknown session")
    def test_6732c1ce_observers_empty_set_for_unknown_session(self):
        """An unknown session returns an empty set."""
        with autotest.step("Arrange: a gateway with no connected observers"):
            gw = WebSocketGateway()

        with autotest.step("Act+Assert: observers('unknown') returns an empty set"):
            assert_equal(gw.observers("unknown"), set(), "observers")

    @autotest.num("3257")
    @autotest.external_id("0ddb3d16-7230-4099-8414-53d0016e20f2")
    @autotest.name("WebSocketGateway: multiple observers can connect to a single session")
    def test_0ddb3d16_multiple_observers_per_session(self):
        """Multiple observers can connect to a single session."""
        with autotest.step("Arrange: a gateway and two observers"):
            gw = WebSocketGateway()
            ws1, ws2 = object(), object()

        with autotest.step("Act: connect both observers to the same session"):
            gw.connect_observer("s1", ws1)
            gw.connect_observer("s1", ws2)

        with autotest.step("Assert: both are registered"):
            assert_in(ws1, gw.observers("s1"), "ws1")
            assert_in(ws2, gw.observers("s1"), "ws2")

        with autotest.step("Act: disconnect one observer"):
            gw.disconnect_observer("s1", ws1)

        with autotest.step("Assert: only the disconnected observer is removed"):
            assert_false(ws1 in gw.observers("s1"), "ws1 absent")
            assert_in(ws2, gw.observers("s1"), "ws2")
