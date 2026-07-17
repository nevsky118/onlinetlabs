"""Characterization of the session routers' route table.

Pins the exact set of (method, path) registered under /users/me/sessions
(via sessions.router) and separately under /sessions (agent_activity, registered
in main.py via a separate include_router with a different prefix, NOT via sessions.router).
Separately pins that the literal `/queue-status` resolves before the catch-all
`/{session_id}`. With the wrong registration order, queue-status would be
swallowed by the query router's catch-all.

The test must stay green before and after consolidating the 8 router files
into commands.py/queries.py/ws.py, that is exactly the point of this characterization.
"""

from fastapi import FastAPI
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from starlette.routing import Match

from sessions.router import router as sessions_router
from sessions.routers.queries import agent_activity_router

pytestmark = []

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
    ("PATCH", "/users/me/sessions/{session_id}"),
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
    """Reproduces exactly how main.py mounts the session routers."""
    app = FastAPI()
    app.include_router(sessions_router, prefix="/users/me/sessions", tags=["sessions"])
    app.include_router(agent_activity_router, prefix="/sessions", tags=["observability"])
    return app


def _route_table(app: FastAPI) -> set[tuple[str, str]]:
    rows: set[tuple[str, str]] = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if not path or not (path.startswith("/users/me/sessions") or path.startswith("/sessions")):
            continue
        methods = getattr(route, "methods", None)
        if methods:
            rows.update((m, path) for m in methods)
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
    @autotest.name("router wiring: набор (method, path) сессионных роутеров не изменился")
    def test_65a828fd_route_table_matches_pinned_set(self):
        app = _build_app()
        with autotest.step("Act: собрать (method, path) под /users/me/sessions и /sessions"):
            actual = _route_table(app)
        with autotest.step("Assert: набор идентичен зафиксированному до рефакторинга"):
            assert_equal(actual, _EXPECTED_ROUTES, "маршрутная таблица не изменилась")

    @autotest.num("2511")
    @autotest.external_id("47ed00f3-936e-4e50-baa8-b1b8771959d3")
    @autotest.name("router wiring: GET queue-status не перекрыт catch-all'ом {session_id}")
    def test_47ed00f3_queue_status_not_shadowed_by_session_id_catchall(self):
        app = _build_app()
        with autotest.step("Act: разрешить GET /users/me/sessions/queue-status"):
            route = _first_match(app, "GET", "/users/me/sessions/queue-status")
        with autotest.step("Assert: резолвится в queue_status, а не в get_session_endpoint"):
            assert route is not None, "маршрут не найден"
            assert_equal(route.endpoint.__name__, "queue_status", "резолвится не в тот хендлер")

    @autotest.num("2512")
    @autotest.external_id("5526191c-4cde-45bc-a6b1-657613cdbf0e")
    @autotest.name("router wiring: GET {session_id} по-прежнему резолвится корректно")
    def test_5526191c_session_id_catchall_still_resolves(self):
        app = _build_app()
        with autotest.step("Act: разрешить GET /users/me/sessions/<обычный id>"):
            route = _first_match(app, "GET", "/users/me/sessions/some-session-id")
        with autotest.step("Assert: резолвится в get_session_endpoint"):
            assert route is not None, "маршрут не найден"
            assert_equal(
                route.endpoint.__name__, "get_session_endpoint", "резолвится не в тот хендлер"
            )
