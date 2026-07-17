"""Корневой conftest для backend/tests.

Дублирует (идемпотентно, через setdefault) env-bootstrap из tests/unit/conftest.py,
чтобы тесты вне tests/unit/ тоже получали дефолтные env vars до импорта
config-зависимых модулей. tests/unit/conftest.py не трогаем — на нём уже
завязаны существующие unit-тесты, миграция бы увеличивала риск без выгоды.
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

# Kill-switch (см. REFACTOR_ANALYSIS.md §5.8): unit-тесты никогда не должны
# бить в реальную LLM. Агентные тесты подменяют модель на pydantic_ai.models.test.TestModel,
# который check_allow_model_requests() не вызывает — их ALLOW_MODEL_REQUESTS=False
# не касается. Реальные модели (agents/base.py, OpenAI-совместимый клиент, в т.ч.
# Yandex GPT) вызывают check_allow_model_requests() внутри Model.request/request_stream
# и упадут RuntimeError, если тест случайно забудет подменить модель.
pydantic_ai_models.ALLOW_MODEL_REQUESTS = False


@pytest.fixture
async def sqlite_session_factory():
    """Фабрика in-memory SQLite сессий для тестов, параметризуемая списком таблиц.

    Убирает copy-paste engine+create, размазанный по ~36 файлам. Использование:

        factory = await sqlite_session_factory([User.__table__, Lab.__table__])
        async with factory() as db:
            db.add(User(...))
            await db.commit()

    Можно вызывать несколько раз в одном тесте — каждый вызов создаёт свой
    независимый engine; все они disposed в конце теста.
    """
    engines: list = []

    async def _make(tables) -> async_sessionmaker:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            # SQLite не форсит FK по умолчанию, но существующие тесты явно
            # выключают его — сохраняем то же поведение для новых таблиц с FK.
            await conn.execute(text("PRAGMA foreign_keys = OFF"))
            for table in tables:
                await conn.run_sync(table.create)
        engines.append(engine)
        return async_sessionmaker(engine, expire_on_commit=False)

    yield _make

    for engine in engines:
        await engine.dispose()
