"""Tests for the observer registry in WebSocketGateway."""

import pytest
from mcp_sdk.testing import autotest

from sessions.ws.gateway import WebSocketGateway

pytestmark = [pytest.mark.unit]


@autotest.num("3255")
@autotest.external_id("407ff2b0-076b-4652-a4db-0cbdf683e02a")
@autotest.name("WebSocketGateway: observer is added to and removed from the registry")
def test_407ff2b0_observer_registry():
    """Observer is added to/removed from the registry."""
    gw = WebSocketGateway()
    ws = object()
    gw.connect_observer("s1", ws)
    assert ws in gw.observers("s1")
    gw.disconnect_observer("s1", ws)
    assert ws not in gw.observers("s1")


@autotest.num("3256")
@autotest.external_id("6732c1ce-eb4c-4bbd-a4e4-330df6fb81ee")
@autotest.name("WebSocketGateway.observers: returns an empty set for an unknown session")
def test_6732c1ce_observers_empty_set_for_unknown_session():
    """An unknown session returns an empty set."""
    gw = WebSocketGateway()
    assert gw.observers("unknown") == set()


@autotest.num("3257")
@autotest.external_id("0ddb3d16-7230-4099-8414-53d0016e20f2")
@autotest.name("WebSocketGateway: multiple observers can connect to a single session")
def test_0ddb3d16_multiple_observers_per_session():
    """Multiple observers can connect to a single session."""
    gw = WebSocketGateway()
    ws1, ws2 = object(), object()
    gw.connect_observer("s1", ws1)
    gw.connect_observer("s1", ws2)
    assert ws1 in gw.observers("s1")
    assert ws2 in gw.observers("s1")
    gw.disconnect_observer("s1", ws1)
    assert ws1 not in gw.observers("s1")
    assert ws2 in gw.observers("s1")
