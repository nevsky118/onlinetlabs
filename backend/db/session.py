import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings


def _unique_prepared_statement_name() -> str:
    """Генерирует уникальное имя prepared statement, чтобы они не конфликтовали при пулинге pgbouncer."""
    # pgbouncer transaction-mode pooling shares backend connections between
    # clients, so prepared statement names must be unique per query.
    return f"__asyncpg_{uuid.uuid4()}__"


engine = create_async_engine(
    settings.database.async_url,
    echo=settings.database.sql_echo,
    pool_size=20,
    max_overflow=30,
    pool_timeout=10,
    pool_recycle=300,
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": _unique_prepared_statement_name,
    },
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    """FastAPI-зависимость: сессия БД + commit на границе запроса, rollback при исключении."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


def get_db_factory():
    """Возвращает фабрику сессий для создания сессий БД вне контекста запроса."""
    return async_session
