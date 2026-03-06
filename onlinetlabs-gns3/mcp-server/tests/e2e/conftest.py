# E2E conftest — пропуск если GNS3 недоступен, auth через admin.

import os

import httpx
import pytest

GNS3_BASE_URL = os.getenv("GNS3_URL", "http://localhost:3080")
GNS3_ADMIN_USER = os.getenv("GNS3_ADMIN_USER", "admin")
GNS3_ADMIN_PASSWORD = os.getenv("GNS3_ADMIN_PASSWORD", "admin")


def _gns3_available() -> bool:
    """Проверка доступности GNS3 сервера."""
    try:
        response = httpx.get(f"{GNS3_BASE_URL}/v3/version", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def _get_admin_token() -> str | None:
    """Получить JWT через admin credentials."""
    try:
        response = httpx.post(
            f"{GNS3_BASE_URL}/v3/access/users/authenticate",
            json={"username": GNS3_ADMIN_USER, "password": GNS3_ADMIN_PASSWORD},
            timeout=5,
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception:
        pass
    return None


def pytest_collection_modifyitems(config, items):
    """Пропустить e2e тесты если GNS3 недоступен."""
    if _gns3_available():
        return
    skip_marker = pytest.mark.skip(reason="GNS3 server not available")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def gns3_url() -> str:
    return GNS3_BASE_URL


@pytest.fixture(scope="session")
def admin_token() -> str:
    """Admin JWT для GNS3 API."""
    token = _get_admin_token()
    if not token:
        pytest.skip("Cannot get admin token")
    return token


@pytest.fixture
async def gns3_client(admin_token):
    """Async httpx client для GNS3 с admin auth."""
    async with httpx.AsyncClient(
        base_url=GNS3_BASE_URL,
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=30,
    ) as client:
        yield client


@pytest.fixture
def api_client(gns3_client):
    """GNS3ApiClient из реального httpx клиента."""
    from src.api_client import GNS3ApiClient
    return GNS3ApiClient(gns3_client)
