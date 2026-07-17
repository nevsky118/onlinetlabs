"""CRUD for validation_runs."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.validation_run import ValidationRun


async def list_for_session(
    db: AsyncSession, session_id: str, limit: int = 20
) -> list[ValidationRun]:
    """Return the session's most recent validation runs, newest first."""
    result = await db.execute(
        select(ValidationRun)
        .where(ValidationRun.session_id == session_id)
        .order_by(ValidationRun.started_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_one(db: AsyncSession, run_id: str) -> ValidationRun | None:
    """Return the run by id. None if it doesn't exist."""
    return await db.get(ValidationRun, run_id)


async def create_run(db: AsyncSession, session_id: str, lab_slug: str) -> str:
    """Create a run in running status and return its id."""
    run_id = str(uuid4())
    row = ValidationRun(
        id=run_id,
        session_id=session_id,
        lab_slug=lab_slug,
        status="running",
        steps=[],
    )
    db.add(row)
    await db.commit()
    return run_id


async def finish_run(db: AsyncSession, run_id: str, status: str, steps: list) -> None:
    """Finish the run: record status, steps, and finish time."""
    row = await db.get(ValidationRun, run_id)
    if row is None:
        return
    row.status = status
    row.steps = steps
    row.finished_at = datetime.now(UTC)
    await db.commit()
