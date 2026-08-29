"""What api.register() actually produces: prefixes, and who stamps session liveness.

Every router now declares its own prefix and tags, so the one thing worth
pinning here is the result: the mounted paths, and the dependency that keeps a
working student from being reclaimed as idle. That dependency binds an HTTP
Request, which a websocket cannot provide, so the websocket routes must stay
without it.
"""

import ast
import pathlib

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute, APIWebSocketRoute
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

import api

pytestmark = [pytest.mark.unit]

_BACKEND = pathlib.Path(__file__).resolve().parents[2]
_LIVENESS = "touch_path_session"

# Prefixes that mark a route as belonging to one learner's live session.
_SESSION_SCOPED = ("/users/me/sessions", "/sessions/{sid}/validation-runs")


def _app() -> FastAPI:
    app = FastAPI()
    api.register(app)
    return app


def _has_liveness(route) -> bool:
    return any(
        dependency.call is not None and dependency.call.__name__ == _LIVENESS
        for dependency in route.dependant.dependencies
    )


class TestApiWiring:
    @autotest.num("3462")
    @autotest.external_id("51e3d141-6c7b-49fa-b15b-f6c86dc2dcf1")
    @autotest.name("api: every session-scoped HTTP route stamps liveness")
    def test_51e3d141_session_routes_stamp_liveness(self):
        with autotest.step("Arrange: the application as main.py builds it"):
            routes = [
                routeoute_2 for routeoute_2 in _app().routes if isinstance(routeoute_2, APIRoute)
            ]

        with autotest.step("Act: find session-scoped routes that do not stamp liveness"):
            missing = sorted(
                routeoute_2.path
                for routeoute_2 in routes
                if routeoute_2.path.startswith(_SESSION_SCOPED) and not _has_liveness(routeoute_2)
            )

        with autotest.step("Assert: none, or the idle reclaimer kills working students"):
            assert_equal(missing, [], "all session routes stamp liveness")

    @autotest.num("3463")
    @autotest.external_id("f88f6bda-d6ca-4dab-8fc9-2889b82cf4be")
    @autotest.name("api: no websocket route carries the HTTP-only liveness dependency")
    def test_f88f6bda_websockets_have_no_http_dependency(self):
        with autotest.step("Arrange: the websocket routes"):
            sockets = [
                routeocket
                for routeocket in _app().routes
                if isinstance(routeocket, APIWebSocketRoute)
            ]

        with autotest.step("Act: look for the HTTP-only dependency on them"):
            offenders = sorted(
                routeocket.path for routeocket in sockets if _has_liveness(routeocket)
            )

        with autotest.step("Assert: none, or every websocket handshake raises TypeError"):
            assert_equal(sockets != [], True, "websocket routes exist")
            assert_equal(offenders, [], "websockets stay free of it")

    @autotest.num("3464")
    @autotest.external_id("766b8c0f-2cc4-4b95-9012-a9f0201f8d08")
    @autotest.name("api: mounting passes no prefix, tags or dependencies of its own")
    def test_766b8c0f_api_only_includes(self):
        with autotest.step("Arrange: the source of api.register"):
            tree = ast.parse((_BACKEND / "api.py").read_text())

        with autotest.step("Act: collect keyword arguments given to include_router"):
            kwargs = []
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "include_router"
                ):
                    kwargs.extend(kw.arg for kw in node.keywords)

        with autotest.step("Assert: routers describe themselves"):
            assert_equal(sorted(kwargs), [], "no prefix/tags/dependencies in api.py")

    @autotest.num("3465")
    @autotest.external_id("ada8908c-a5d0-4257-8ed5-02ca9fa73bc7")
    @autotest.name("api: every documented route carries a tag")
    def test_ada8908c_every_route_is_tagged(self):
        with autotest.step("Arrange: the application as main.py builds it"):
            app = _app()

        with autotest.step("Act: find documented routes with no tag"):
            # websocket routes never reach OpenAPI, so FastAPI gives them no tags
            untagged = sorted(
                route.path for route in app.routes if isinstance(route, APIRoute) and not route.tags
            )

        with autotest.step("Assert: none, so the OpenAPI page stays grouped"):
            assert_equal(untagged, [], "all routes tagged")
