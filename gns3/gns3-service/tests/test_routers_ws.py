"""Unit tests for the ws WebSocket router."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp_sdk.testing import autotest
from starlette.websockets import WebSocketDisconnect

from src.config import settings
from src.routers.ws import router as ws_router


def _build_app() -> FastAPI:
    """Minimal application with the ws router and app.state stubs."""
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
    """Without a valid internal_api_token the connection must close with 1008."""

    @autotest.num("3365")
    @autotest.external_id("d0f93911-95b8-406e-a74b-1bdb0071af35")
    @autotest.name("WS events endpoint: closes with 1008 when the token is missing")
    def test_d0f93911_close_1008_when_token_missing(self, app, monkeypatch):
        with autotest.step("Arrange: set the expected internal token"):
            # Make sure the token in settings is non-empty, otherwise the guard just lets it through.
            monkeypatch.setattr(
                settings.security, "internal_api_token", "expected-token", raising=False
            )

        with autotest.step("Act + Assert: connecting without a token closes with code 1008"):
            with TestClient(app) as client:
                with pytest.raises(WebSocketDisconnect) as excinfo:
                    with client.websocket_connect(
                        "/sessions/11111111-1111-1111-1111-111111111111/events"
                    ) as ws:
                        ws.receive_text()
                assert excinfo.value.code == 1008

    @autotest.num("3366")
    @autotest.external_id("5a767d5c-5066-4203-8ead-be43c660b827")
    @autotest.name("WS events endpoint: closes with 1008 when the token is wrong")
    def test_5a767d5c_close_1008_when_token_wrong(self, app, monkeypatch):
        with autotest.step("Arrange: set the expected internal token"):
            monkeypatch.setattr(
                settings.security, "internal_api_token", "expected-token", raising=False
            )

        with autotest.step("Act + Assert: connecting with the wrong token closes with code 1008"):
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
    @autotest.num("3367")
    @autotest.external_id("34ce72d7-834a-4419-a967-8b8c68e7b73c")
    @autotest.name("WS events endpoint: full happy path (skipped, covered by e2e)")
    def test_34ce72d7_ws_happy_path(self):
        pass
