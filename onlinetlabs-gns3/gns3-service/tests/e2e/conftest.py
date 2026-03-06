# E2E conftest — GNS3 + PostgreSQL.

import os

import httpx
import pytest

GNS3_URL = os.getenv("GNS3_URL", "http://localhost:3080")
GNS3_ADMIN_USER = os.getenv("GNS3_ADMIN_USER", "admin")
GNS3_ADMIN_PASSWORD = os.getenv("GNS3_ADMIN_PASSWORD", "admin")
DB_URL = os.getenv(
    "TEST_DB_URL",
    "postgresql+asyncpg://gns3test:gns3test@localhost:5433/gns3_service_test",
)


def _gns3_available() -> bool:
    try:
        response = httpx.get(f"{GNS3_URL}/v3/version", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    if _gns3_available():
        return
    skip_marker = pytest.mark.skip(reason="GNS3/PostgreSQL not available")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture(scope="session")
async def setup_db():
    """Создать таблицы для e2e тестов."""
    from src.db.session import create_tables

    await create_tables(DB_URL)


@pytest.fixture
async def admin_client():
    from src.gns3_admin_client import GNS3AdminClient

    client = GNS3AdminClient(GNS3_URL, GNS3_ADMIN_USER, GNS3_ADMIN_PASSWORD)
    await client.authenticate()
    yield client
    await client.close()


@pytest.fixture
async def db_session():
    from src.db.session import create_session_factory

    factory = create_session_factory(DB_URL)
    async with factory() as session:
        yield session


@pytest.fixture
async def template_project(admin_client):
    """Создать template project, удалить после теста."""
    import uuid

    name = f"e2e-template-{uuid.uuid4().hex[:8]}"
    response = await admin_client._client.post("/v3/projects", json={"name": name})
    project = response.json()
    pid = project["project_id"]
    yield pid
    try:
        await admin_client._client.delete(f"/v3/projects/{pid}")
    except Exception:
        pass


@pytest.fixture
async def session_result(admin_client, db_session, setup_db, template_project):
    """Создать сессию, вернуть результат, cleanup после теста."""
    import uuid

    from src.service import SessionService

    svc = SessionService(admin_client=admin_client, gns3_url=GNS3_URL)
    user_id = uuid.uuid4().hex[:16]
    result = await svc.create_session(
        db=db_session, user_id=user_id, template_project_id=template_project,
    )
    yield result
    try:
        await svc.delete_session(db=db_session, session_id=result.session_id)
    except Exception:
        pass
    # cleanup leftover GNS3 resources
    for cleanup in [
        lambda: admin_client._client.delete(f"/v3/projects/{result.project_id}"),
        lambda: admin_client._client.delete(f"/v3/access/users/{result.gns3_user_id}"),
    ]:
        try:
            await cleanup()
        except Exception:
            pass
