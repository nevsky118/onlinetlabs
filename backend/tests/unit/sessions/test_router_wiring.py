"""Characterization of the session routers' route table.

Pins the exact set of (method, path) the session routers declare: /users/me/sessions
for commands, queries and websockets, /sessions for agent_activity, which is a
separate router and not part of sessions.router. Separately pins that the literal
`/queue-status` resolves before the catch-all `/{session_id}`. With the wrong
registration order, queue-status would be swallowed by the query router's catch-all.

The prefixes now live on the routers themselves, so this test mounts them the way
api.py does: with no arguments.
"""

import pytest
from fastapi import FastAPI
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_not_none
from starlette.routing import Match

from sessions.router import router as sessions_router
from sessions.router import ws_router
from sessions.routers.queries import agent_activity_router

pytestmark = [pytest.mark.unit]

# Exact set of (method, path), collected from the current (pre-refactor) code.
_EXPECTED_ROUTES = {
    ("GET", "/sessions/{session_id}/agent-activity"),
    ("GET", "/users/me/sessions"),
    ("GET", "/users/me/sessions/queue-status"),
    ("GET", "/users/me/sessions/{session_id}"),
    ("GET", "/users/me/sessions/{session_id}/activity"),
    ("GET", "/users/me/sessions/{session_id}/chat"),
    ("GET", "/users/me/sessions/{session_id}/credentials"),
    ("GET", "/users/me/sessions/{session_id}/state"),
    ("POST", "/users/me/sessions"),
    ("POST", "/users/me/sessions/{session_id}/end"),
    ("POST", "/users/me/sessions/{session_id}/nodes/{action}"),
    ("POST", "/users/me/sessions/{session_id}/nodes/{node_id}/{action}"),
    ("POST", "/users/me/sessions/{session_id}/reset"),
    ("POST", "/users/me/sessions/{session_id}/restart"),
    ("POST", "/users/me/sessions/{session_id}/stop"),
    ("WS", "/users/me/sessions/ws/observe/{session_id}"),
    ("WS", "/users/me/sessions/ws/sessions/{session_id}"),
    ("WS", "/users/me/sessions/ws/{session_id}/events"),
}


def _build_app() -> FastAPI:
    """Mounts the session routers exactly as api.py does."""
    app = FastAPI()
    app.include_router(sessions_router)
    app.include_router(ws_router)
    app.include_router(agent_activity_router)
    return app


def _route_table(app: FastAPI) -> set[tuple[str, str]]:
    rows: set[tuple[str, str]] = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if not path or not (path.startswith("/users/me/sessions") or path.startswith("/sessions")):
            continue
        methods = getattr(route, "methods", None)
        if methods:
            rows.update((method, path) for method in methods)
        else:
            rows.add(("WS", path))
    return rows


def _first_match(app: FastAPI, method: str, path: str):
    scope = {"type": "http", "method": method, "path": path}
    for route in app.routes:
        match, _ = route.matches(scope)
        if match == Match.FULL:
            return route
    return None


class TestSessionRouterWiring:
    @autotest.num("2510")
    @autotest.external_id("65a828fd-599b-4817-a47a-5493fe707ffc")
    @autotest.name("router wiring: the (method, path) set of session routers is unchanged")
    def test_65a828fd_route_table_matches_pinned_set(self):
        with autotest.step("Arrange: build the app as main.py mounts it"):
            app = _build_app()
        with autotest.step("Act: collect (method, path) under /users/me/sessions and /sessions"):
            actual = _route_table(app)
        with autotest.step("Assert: set is identical to the one pinned before the refactor"):
            assert_equal(actual, _EXPECTED_ROUTES, "route table unchanged")

    @autotest.num("2511")
    @autotest.external_id("47ed00f3-936e-4e50-baa8-b1b8771959d3")
    @autotest.name("router wiring: GET queue-status is not shadowed by the {session_id} catch-all")
    def test_47ed00f3_queue_status_not_shadowed_by_session_id_catchall(self):
        with autotest.step("Arrange: build the app as main.py mounts it"):
            app = _build_app()
        with autotest.step("Act: resolve GET /users/me/sessions/queue-status"):
            route = _first_match(app, "GET", "/users/me/sessions/queue-status")
        with autotest.step("Assert: resolves to queue_status, not get_session_endpoint"):
            assert_is_not_none(route, "route not found")
            assert_equal(route.endpoint.__name__, "queue_status", "resolved to the wrong handler")

    @autotest.num("2512")
    @autotest.external_id("5526191c-4cde-45bc-a6b1-657613cdbf0e")
    @autotest.name("router wiring: GET {session_id} still resolves correctly")
    def test_5526191c_session_id_catchall_still_resolves(self):
        with autotest.step("Arrange: build the app as main.py mounts it"):
            app = _build_app()
        with autotest.step("Act: resolve GET /users/me/sessions/<regular id>"):
            route = _first_match(app, "GET", "/users/me/sessions/some-session-id")
        with autotest.step("Assert: resolves to get_session_endpoint"):
            assert_is_not_none(route, "route not found")
            assert_equal(
                route.endpoint.__name__, "get_session_endpoint", "resolved to the wrong handler"
            )
