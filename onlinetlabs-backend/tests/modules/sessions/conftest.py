import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from models.lab import Lab
from models.user import User


@pytest_asyncio.fixture()
async def session_user(db_session: AsyncSession) -> User:
    user = User(id="session-user-001", name="Session User", email="session@test.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def session_lab(db_session: AsyncSession) -> Lab:
    lab = Lab(
        slug="session-lab-1",
        title="Session Lab",
        difficulty="beginner",
        environment_type="docker",
        order_in_course=0,
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab
