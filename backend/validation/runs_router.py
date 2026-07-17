"""GET /sessions/{sid}/validation-runs[/{runId}] — run history."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from sessions.services.query import get_owned_session
from validation.repository import get_one, list_for_session
from validation.schemas import ValidationRunDetail, ValidationRunListItem

router = APIRouter()


def _count_checks(steps: list) -> tuple[int, int]:
    """Count passed and total checks across steps."""
    total = 0
    passed = 0
    for step in steps:
        checks = step.get("checks") if isinstance(step, dict) else None
        if not isinstance(checks, list):
            continue
        for check in checks:
            total += 1
            if isinstance(check, dict) and check.get("ok") is True:
                passed += 1
    return passed, total


@router.get("/{sid}/validation-runs", response_model=list[ValidationRunListItem])
async def list_runs(
    sid: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the session's validation runs with a checks summary."""
    session = await get_owned_session(db, sid, current_user["id"])
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    runs = await list_for_session(db, sid, limit=20)
    items: list[ValidationRunListItem] = []
    for run in runs:
        if run.finished_at is not None and run.started_at is not None:
            duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
            passed, total = _count_checks(run.steps or [])
        else:
            duration_ms = None
            passed = None  # type: ignore[assignment]
            total = None  # type: ignore[assignment]
        items.append(
            ValidationRunListItem(
                id=run.id,
                lab_slug=run.lab_slug,
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                duration_ms=duration_ms,
                passed_checks=passed,
                total_checks=total,
            )
        )
    return items


@router.get("/{sid}/validation-runs/{run_id}", response_model=ValidationRunDetail)
async def get_run(
    sid: str,
    run_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a single validation run with detailed steps."""
    session = await get_owned_session(db, sid, current_user["id"])
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    run = await get_one(db, run_id)
    if run is None or run.session_id != sid:
        raise HTTPException(status_code=404, detail="Validation run not found")
    return ValidationRunDetail(
        id=run.id,
        lab_slug=run.lab_slug,
        status=run.status,
        steps=run.steps or [],
        started_at=run.started_at,
        finished_at=run.finished_at,
    )
