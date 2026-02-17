import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import Course
from models.lab import Lab


@pytest_asyncio.fixture()
async def sample_course(db_session: AsyncSession) -> Course:
    course = Course(
        slug="net-101", title="Networking 101", difficulty="beginner", order=1
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest_asyncio.fixture()
async def sample_lab_in_course(db_session: AsyncSession, sample_course: Course) -> Lab:
    lab = Lab(
        slug="lab-ping",
        title="Ping Lab",
        difficulty="beginner",
        course_slug=sample_course.slug,
        environment_type="gns3",
        order_in_course=1,
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab
