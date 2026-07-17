"""Tests for the observer registry in WebSocketGateway."""

import pytest

from sessions.ws.gateway import WebSocketGateway

pytestmark = [pytest.mark.unit]


def test_observer_registry():
    """Observer is added to/removed from the registry."""
    gw = WebSocketGateway()
    ws = object()
    gw.connect_observer("s1", ws)
    assert ws in gw.observers("s1")
    gw.disconnect_observer("s1", ws)
    assert ws not in gw.observers("s1")


def test_observers_empty_set_for_unknown_session():
    """An unknown session returns an empty set."""
    gw = WebSocketGateway()
    assert gw.observers("unknown") == set()


def test_multiple_observers_per_session():
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
