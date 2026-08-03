"""The published port must not expose session or history data without the internal token.

The router unit tests build their own FastAPI app and include routers directly, so they
do not exercise the include-time dependency. These assert it on the real app.
"""

import pytest
from fastapi.testclient import TestClient
from mcp_sdk.testing import autotest

from src.main import app

_SESSION_ID = "11111111-1111-1111-1111-111111111111"
_GUARDED = [
    f"/sessions/{_SESSION_ID}/state",
    f"/sessions/{_SESSION_ID}/activity",
    f"/history/{_SESSION_ID}/actions",
]


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.parametrize("path", _GUARDED)
@autotest.num("3349")
@autotest.external_id("c18bfbf6-bd1d-4cf6-828b-5d721e2ef7d9")
@autotest.name("Guarded routes: reject requests missing the internal token")
def test_c18bfbf6_guarded_paths_reject_missing_token(client, path):
    with autotest.step("Act+Assert: request without the internal token is rejected with 403"):
        assert client.get(path).status_code == 403


@pytest.mark.parametrize("path", _GUARDED)
@autotest.num("3350")
@autotest.external_id("a332ad01-e226-40ef-933b-79bcf127a389")
@autotest.name("Guarded routes: reject requests with the wrong internal token")
def test_a332ad01_guarded_paths_reject_wrong_token(client, path):
    with autotest.step("Act: request with the wrong internal token"):
        response = client.get(path, headers={"Authorization": "Bearer wrong-token"})

    with autotest.step("Assert: rejected with 403"):
        assert response.status_code == 403


@autotest.num("3351")
@autotest.external_id("5fe99ff7-1ccd-4f41-ad88-34874ae2b7ce")
@autotest.name("Guarded routes: reject a malformed Authorization header")
def test_5fe99ff7_guarded_paths_reject_malformed_authorization(client):
    with autotest.step("Act: request with a malformed Authorization header (missing 'Bearer')"):
        response = client.get(_GUARDED[0], headers={"Authorization": "test-internal-token"})

    with autotest.step("Assert: rejected with 403"):
        assert response.status_code == 403


@autotest.num("3352")
@autotest.external_id("0edff9c7-7028-484c-a453-e6e79c79ffff")
@autotest.name("Guarded routes: /health stays open without a token")
def test_0edff9c7_health_stays_open(client):
    # The container healthcheck calls it unauthenticated; any status but 403 is fine.
    with autotest.step("Act+Assert: /health without a token is not rejected with 403"):
        assert client.get("/health").status_code != 403
