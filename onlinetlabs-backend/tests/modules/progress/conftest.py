import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import Course
from models.lab import Lab, LabStep
from models.user import User


@pytest_asyncio.fixture()
async def progress_user(db_session: AsyncSession) -> User:
    user = User(id="progress-user-001", name="Progress User", email="progress@test.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def progress_course(db_session: AsyncSession) -> Course:
    course = Course(
        slug="prog-101", title="Progress Course", difficulty="beginner", order=1
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest_asyncio.fixture()
async def progress_lab(db_session: AsyncSession, progress_course: Course) -> Lab:
    lab = Lab(
        slug="prog-lab-1",
        title="Progress Lab",
        difficulty="beginner",
        course_slug=progress_course.slug,
        environment_type="docker",
        order_in_course=1,
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab


@pytest_asyncio.fixture()
async def progress_lab_steps(
    db_session: AsyncSession, progress_lab: Lab
) -> list[LabStep]:
    steps = [
        LabStep(
            lab_slug=progress_lab.slug,
            slug="ps-1",
            title="Step 1",
            step_order=1,
            validation_type="command",
        ),
        LabStep(
            lab_slug=progress_lab.slug,
            slug="ps-2",
            title="Step 2",
            step_order=2,
            validation_type="output",
        ),
    ]
    db_session.add_all(steps)
    await db_session.commit()
    return steps
