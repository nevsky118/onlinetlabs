import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import Course
from models.lab import Lab, LabStep


@pytest_asyncio.fixture()
async def sample_course_for_labs(db_session: AsyncSession) -> Course:
    course = Course(
        slug="net-201", title="Networking 201", difficulty="intermediate", order=2
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest_asyncio.fixture()
async def sample_lab(db_session: AsyncSession, sample_course_for_labs: Course) -> Lab:
    lab = Lab(
        slug="lab-traceroute",
        title="Traceroute Lab",
        difficulty="intermediate",
        course_slug=sample_course_for_labs.slug,
        environment_type="gns3",
        order_in_course=1,
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)

    steps = [
        LabStep(
            lab_slug=lab.slug,
            slug="step-1",
            title="Open terminal",
            step_order=1,
            validation_type="command",
        ),
        LabStep(
            lab_slug=lab.slug,
            slug="step-2",
            title="Run traceroute",
            step_order=2,
            validation_type="output",
        ),
    ]
    db_session.add_all(steps)
    await db_session.commit()
    return lab


@pytest_asyncio.fixture()
async def sample_standalone_lab(db_session: AsyncSession) -> Lab:
    lab = Lab(
        slug="lab-standalone",
        title="Standalone Lab",
        difficulty="beginner",
        environment_type="docker",
        order_in_course=0,
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab
