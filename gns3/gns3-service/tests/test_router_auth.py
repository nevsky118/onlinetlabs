"""The published port must not expose session or history data without the internal token.

The router unit tests build their own FastAPI app and include routers directly, so they
do not exercise the include-time dependency. These assert it on the real app.
"""

import pytest
from fastapi.testclient import TestClient

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
def test_guarded_paths_reject_missing_token(client, path):
    assert client.get(path).status_code == 403


@pytest.mark.parametrize("path", _GUARDED)
def test_guarded_paths_reject_wrong_token(client, path):
    response = client.get(path, headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 403


def test_guarded_paths_reject_malformed_authorization(client):
    response = client.get(_GUARDED[0], headers={"Authorization": "test-internal-token"})
    assert response.status_code == 403


def test_health_stays_open(client):
    # The container healthcheck calls it unauthenticated; any status but 403 is fine.
    assert client.get("/health").status_code != 403
