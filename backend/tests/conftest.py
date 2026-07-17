"""Root conftest for backend/tests.

Duplicates (idempotently, via setdefault) the env bootstrap from tests/unit/conftest.py,
so tests outside tests/unit/ also get default env vars before importing
config-dependent modules. We don't touch tests/unit/conftest.py itself, since
existing unit tests already depend on it and migrating it would add risk without benefit.
"""

import os

_TEST_ENV_DEFAULTS = {
    "DB_USER": "test",
    "DB_PASSWORD": "test",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "test",
    "REDIS_URL": "redis://localhost:6379/0",
    "ENVIRONMENT": "test",
    "JWT_SECRET": "test-jwt-secret",
    "LOG_LEVEL": "DEBUG",
    "CRED_ENCRYPTION_KEY": "r1juy4ePJMqjrYbqXaCw7kDPq8Gwudckyv0wiIBIwfU=",
    "INTERNAL_API_TOKEN": "test-internal-token",
    "YANDEX_API_KEY": "sk-test",
    "YANDEX_FOLDER": "test-folder",
    "AGENTS_CHAT_MODEL": "yandex-gpt-5.1",
    "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
    "FRONTEND_URL": "http://localhost:3000",
    "GNS3_SERVICE_URL": "http://localhost:8101",
    "GNS3_PUBLIC_URL": "http://localhost:3080",
    "GNS3_INTERNAL_URL": "http://localhost:3080",
    "MCP_SERVER_URL": "http://localhost:8100",
}
for _key, _value in _TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)

import pydantic_ai.models as pydantic_ai_models
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Kill switch (see REFACTOR_ANALYSIS.md §5.8): unit tests must never hit a real
# LLM. Agent tests swap in pydantic_ai.models.test.TestModel, which doesn't call
# check_allow_model_requests(), so ALLOW_MODEL_REQUESTS=False doesn't affect them.
# Real models (agents/base.py, the OpenAI-compatible client, incl. Yandex GPT)
# call check_allow_model_requests() inside Model.request/request_stream and will
# raise RuntimeError if a test accidentally forgets to swap the model.
pydantic_ai_models.ALLOW_MODEL_REQUESTS = False


@pytest.fixture
async def sqlite_session_factory():
    """Factory for in-memory SQLite sessions for tests, parameterized by a list of tables.

    Removes the copy-pasted engine+create boilerplate spread across ~36 files. Usage:

        factory = await sqlite_session_factory([User.__table__, Lab.__table__])
        async with factory() as db:
            db.add(User(...))
            await db.commit()

    Can be called multiple times in the same test; each call creates its own
    independent engine, and all of them are disposed at the end of the test.
    """
    engines: list = []

    async def _make(tables) -> async_sessionmaker:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            # SQLite doesn't enforce FKs by default, but existing tests
            # explicitly disable it too, keeping the same behavior for new tables with FKs.
            await conn.execute(text("PRAGMA foreign_keys = OFF"))
            for table in tables:
                await conn.run_sync(table.create)
        engines.append(engine)
        return async_sessionmaker(engine, expire_on_commit=False)

    yield _make

    for engine in engines:
        await engine.dispose()
