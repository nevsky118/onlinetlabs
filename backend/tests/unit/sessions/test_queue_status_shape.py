"""The queue-status body the dashboard reads, pinned field by field."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from auth.dependencies import get_current_user
from sessions.queue import get_queue_service
from sessions.routers.queries import router as queries_router
from tests.settings.data.queue_data import FixedPositionQueueData

pytestmark = [pytest.mark.unit]

_LEARNER = "learner-1"
_LAB = "lan-static-ip"


def _client(queue: FixedPositionQueueData) -> TestClient:
    """An app with the queue and the caller stubbed out."""
    app = FastAPI()
    app.include_router(queries_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": _LEARNER}
    app.dependency_overrides[get_queue_service] = lambda: queue
    return TestClient(app)


class TestQueueStatusShape:
    @autotest.num("3460")
    @autotest.external_id("2e5b71fa-9d84-4c03-b6a7-8f10d3e5c927")
    @autotest.name("queue-status: a waiting learner gets position, depth and eta")
    def test_2e5b71fa_waiting_learner(self):
        with autotest.step("Arrange: the learner is third in line"):
            client = _client(FixedPositionQueueData(3))

        with autotest.step("Act: read the queue status"):
            resp = client.get("/users/me/sessions/queue-status", params={"lab_slug": _LAB})

        with autotest.step("Assert: exactly the four fields the dashboard reads"):
            assert_equal(resp.status_code, 200, "200 OK")
            assert_equal(
                resp.json(),
                {"in_queue": True, "queue_position": 3, "queue_depth": 4, "eta_sec": 90},
                "queued body",
            )

    @autotest.num("3461")
    @autotest.external_id("bb0f4c37-6a25-42de-9c81-73fd0e5a2b46")
    @autotest.name("queue-status: an unqueued learner gets no position or eta keys")
    def test_bb0f4c37_unqueued_learner(self):
        with autotest.step("Arrange: the learner holds no place in line"):
            client = _client(FixedPositionQueueData(None))

        with autotest.step("Act: read the queue status"):
            resp = client.get("/users/me/sessions/queue-status", params={"lab_slug": _LAB})

        with autotest.step("Assert: the two-field body, with no null padding"):
            assert_equal(resp.status_code, 200, "200 OK")
            assert_equal(resp.json(), {"in_queue": False, "queue_depth": 4}, "unqueued body")
