"""Тесты реестра наблюдателей в WebSocketGateway."""

import pytest

from sessions.ws.gateway import WebSocketGateway

pytestmark = [pytest.mark.unit]


def test_observer_registry():
    """Наблюдатель добавляется/удаляется из реестра."""
    gw = WebSocketGateway()
    ws = object()
    gw.connect_observer("s1", ws)
    assert ws in gw.observers("s1")
    gw.disconnect_observer("s1", ws)
    assert ws not in gw.observers("s1")


def test_observers_empty_set_for_unknown_session():
    """Для неизвестной сессии возвращается пусто множество."""
    gw = WebSocketGateway()
    assert gw.observers("unknown") == set()


def test_multiple_observers_per_session():
    """На одну сессию можно подключить несколько наблюдателей."""
    gw = WebSocketGateway()
    ws1, ws2 = object(), object()
    gw.connect_observer("s1", ws1)
    gw.connect_observer("s1", ws2)
    assert ws1 in gw.observers("s1")
    assert ws2 in gw.observers("s1")
    gw.disconnect_observer("s1", ws1)
    assert ws1 not in gw.observers("s1")
    assert ws2 in gw.observers("s1")
