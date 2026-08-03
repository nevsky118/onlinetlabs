"""Guards the assembled app against two routers claiming the same (method, path).

FastAPI resolves the first match, so a later registration is dead code and the
shadowing is silent. Imports the real app, unlike test_router_wiring.py, which
builds a mini app from the session routers alone and cannot see cross-router collisions.
"""

from collections import Counter

from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_not_none
from starlette.routing import Match

from main import app

pytestmark = []


def _route_table() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for route in app.routes:
        path = getattr(route, "path", None)
        if not path:
            continue
        methods = getattr(route, "methods", None)
        rows.extend((m, path) for m in (methods or ["WS"]))
    return rows


class TestAppRouteUniqueness:
    @autotest.num("2653")
    @autotest.external_id("816e6547-e00f-48a1-bcd0-cb2d1f958406")
    @autotest.name("app routes: no (method, path) is registered twice")
    def test_816e6547_no_duplicate_method_path(self):
        with autotest.step("Act: collect (method, path) from every route of the real app"):
            duplicates = sorted(k for k, n in Counter(_route_table()).items() if n > 1)
        with autotest.step("Assert: nothing is registered twice"):
            assert_equal(duplicates, [], "a route is shadowed by an earlier registration")

    @autotest.num("2654")
    @autotest.external_id("7366a3ae-07eb-4f7d-81dd-2711154e70e9")
    @autotest.name("app routes: GET /users/me/sessions resolves to the learning session list")
    def test_7366a3ae_learning_session_list_not_shadowed(self):
        with autotest.step("Arrange: an ASGI scope for GET /users/me/sessions"):
            scope = {"type": "http", "method": "GET", "path": "/users/me/sessions"}

        with autotest.step("Act: resolve GET /users/me/sessions"):
            matched = next(
                (r for r in app.routes if r.matches(scope)[0] == Match.FULL),
                None,
            )
        with autotest.step("Assert: it lands on list_sessions, not on the login session list"):
            assert_is_not_none(matched, "route not found")
            assert_equal(matched.endpoint.__name__, "list_sessions", "wrong handler")
