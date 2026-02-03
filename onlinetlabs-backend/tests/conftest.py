import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base

# ENV_FILE fallback for tests
if not os.getenv("ENV_FILE"):
    _example = Path(__file__).resolve().parent.parent / "local.env.example"
    if _example.exists():
        os.environ["ENV_FILE"] = str(_example)

# Import models to register in metadata
import app.models.user  # noqa: F401
import app.models.course  # noqa: F401
import app.models.lab  # noqa: F401
import app.models.progress  # noqa: F401
import app.models.session  # noqa: F401


def pytest_addoption(parser):
    parser.addoption(
        "--envFile", action="store", default=None, help="Path to .env or .env.aes file"
    )


@pytest.fixture(scope="session")
def config(pytestconfig):
    env_path = pytestconfig.getoption("envFile")
    if env_path:
        os.environ["ENV_FILE"] = env_path
    from config import _load_settings

    _load_settings.cache_clear()
    return _load_settings()


# --- SQLite in-memory engine ---
TEST_DATABASE_URL = "sqlite+aiosqlite://"
_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_async_session_factory = async_sessionmaker(
    bind=_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _create_tables():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture()
async def db_session(_create_tables) -> AsyncGenerator[AsyncSession, None]:
    async with _async_session_factory() as session:
        yield session


def _make_db_override(session_factory):
    async def _override() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    return _override


@pytest_asyncio.fixture()
async def client(_create_tables) -> AsyncGenerator[AsyncClient, None]:
    from main import app
    from app.db.session import get_db

    app.dependency_overrides[get_db] = _make_db_override(_async_session_factory)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
    # Cleanup non-system tables after each test
    async with _engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
