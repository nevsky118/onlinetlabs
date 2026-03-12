from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def create_session_factory(
    database_url: str, echo: bool = False
) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(database_url, echo=echo)
    return async_sessionmaker(engine, expire_on_commit=False)


async def create_tables(database_url: str) -> None:
    from src.db.models import Base

    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
