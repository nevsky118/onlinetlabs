from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import create_backend_token


_MOCK_USER = {
    "id": "test-user-id-001",
    "role": "student",
}


@pytest.fixture()
def mock_user() -> dict:
    return dict(_MOCK_USER)


@pytest_asyncio.fixture()
async def auth_client(_create_tables) -> AsyncGenerator[AsyncClient, None]:
    from main import app
    from app.db.session import get_db
    from tests.conftest import _make_db_override, _async_session_factory

    app.dependency_overrides[get_db] = _make_db_override(_async_session_factory)
    token = create_backend_token(user_id=_MOCK_USER["id"], role=_MOCK_USER["role"])
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {token}"},
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
