"""Unit-тесты WebSocket-роутера ws."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.config import settings
from src.routers.ws import router as ws_router


def _build_app() -> FastAPI:
    """Минимальное приложение с ws-роутером и stub-ами app.state."""
    app = FastAPI()
    app.include_router(ws_router)
    app.state.session_service = AsyncMock()
    app.state.event_broker = AsyncMock()
    app.state.ws_proxy = AsyncMock()
    app.state.db_factory = None
    return app


@pytest.fixture
def app():
    return _build_app()


class TestWsTokenValidation:
    """Без валидного internal_api_token соединение должно закрываться 1008."""

    def test_close_1008_when_token_missing(self, app, monkeypatch):
        # Убедимся, что в settings token непуст — иначе guard просто пропустит.
        monkeypatch.setattr(
            settings.security, "internal_api_token", "expected-token", raising=False
        )
        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with client.websocket_connect(
                    "/sessions/11111111-1111-1111-1111-111111111111/events"
                ) as ws:
                    ws.receive_text()
            assert excinfo.value.code == 1008

    def test_close_1008_when_token_wrong(self, app, monkeypatch):
        monkeypatch.setattr(
            settings.security, "internal_api_token", "expected-token", raising=False
        )
        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with client.websocket_connect(
                    "/sessions/11111111-1111-1111-1111-111111111111/events?token=wrong"
                ) as ws:
                    ws.receive_text()
            assert excinfo.value.code == 1008


@pytest.mark.skip(
    reason=(
        "WS happy path требует EventBroker.subscribe (async iterator), реальную "
        "session-запись в БД и working ws_proxy.start_project — слишком тяжело "
        "для unit-теста, покрыто e2e."
    )
)
class TestWsHappyPath:
    def test_ws_happy_path(self):
        pass
