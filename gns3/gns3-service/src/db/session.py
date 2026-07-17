import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _unique_prepared_statement_name() -> str:
    # pgbouncer transaction-mode pooling reuses backend connections across
    # clients, so each prepared statement name MUST be unique to avoid
    # DuplicatePreparedStatementError on the shared backend.
    return f"__asyncpg_{uuid.uuid4()}__"


def create_session_factory(
    database_url: str, echo: bool = False
) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        database_url,
        echo=echo,
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
    return async_sessionmaker(engine, expire_on_commit=False)
