"""Task 7: тест compute_cohort_metrics через in-memory SQLite."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.experiment import ExperimentMetrics
from models.lab import Lab
from models.progress import LabProgress
from models.session import LearningSession
from models.user import User

pytestmark = [pytest.mark.unit]

_NOW = datetime(2026, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
_SKILL = "static-ip-addressing"


@pytest.fixture
async def cohort_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        # создаём только нужные таблицы (SQLite не форсит FK)
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Lab.__table__.create)
        await conn.run_sync(LabProgress.__table__.create)
        await conn.run_sync(LearningSession.__table__.create)
        await conn.run_sync(ExperimentMetrics.__table__.create)

    l1_start = _NOW - timedelta(days=10)
    l1_end = _NOW - timedelta(days=10, hours=-2)
    l2_start = _NOW - timedelta(days=3)
    l2_end = _NOW - timedelta(days=2)

    async with session_factory() as db:
        db.add(User(id="cohort-u1", email="u1@t.local", name="u1", role="student", control_arm="closed"))
        db.add(Lab(slug="lan-static-ip", title="L1 Static IP", meta={"skill": _SKILL}))
        db.add(Lab(slug="lan-static-ip-b", title="L2 Static IP", meta={"skill": _SKILL}))

        # LabProgress: L1 завершена 10 дней назад, L2 — 2 дня назад
        db.add(LabProgress(
            id="lp-l1", user_id="cohort-u1", lab_slug="lan-static-ip",
            status="completed", started_at=l1_start, completed_at=l1_end,
        ))
        db.add(LabProgress(
            id="lp-l2", user_id="cohort-u1", lab_slug="lan-static-ip-b",
            status="completed", started_at=l2_start, completed_at=l2_end,
        ))

        # LearningSession: по одной сессии на каждую лабу
        db.add(LearningSession(
            id="sess-l1", user_id="cohort-u1", lab_slug="lan-static-ip",
            status="ended", started_at=l1_start, ended_at=l1_end,
        ))
        db.add(LearningSession(
            id="sess-l2", user_id="cohort-u1", lab_slug="lan-static-ip-b",
            status="ended", started_at=l2_start, ended_at=l2_end,
        ))

        # ExperimentMetrics: L1-сессия (без l2_unassisted_pass), L2-сессия (l2_unassisted_pass=True)
        db.add(ExperimentMetrics(
            id="em-l1", session_id="sess-l1", user_id="cohort-u1", lab_slug="lan-static-ip",
            experiment_group="closed", base_arm="closed",
            total_time_seconds=7200.0, steps_completed=5, total_errors=3, repeated_errors=2,
            unique_error_types=2, interventions_received=2, interventions_succeeded=1,
            interventions_failed=0, interventions_accepted=1, escalations=1,
            l2_unassisted_pass=None, final_score=0.8, completed=True,
        ))
        db.add(ExperimentMetrics(
            id="em-l2", session_id="sess-l2", user_id="cohort-u1", lab_slug="lan-static-ip-b",
            experiment_group="closed", base_arm="closed",
            total_time_seconds=3600.0, steps_completed=5, total_errors=0, repeated_errors=0,
            unique_error_types=0, interventions_received=0, interventions_succeeded=0,
            interventions_failed=0, interventions_accepted=0, escalations=0,
            l2_unassisted_pass=True, final_score=1.0, completed=True,
        ))
        await db.commit()

    async with session_factory() as db:
        yield db

    await engine.dispose()


@pytest.fixture
async def censored_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Lab.__table__.create)
        await conn.run_sync(LabProgress.__table__.create)
        await conn.run_sync(LearningSession.__table__.create)
        await conn.run_sync(ExperimentMetrics.__table__.create)

    l1_start = _NOW - timedelta(days=10)
    l1_end = _NOW - timedelta(days=5)

    async with session_factory() as db:
        db.add(User(id="cens-u1", email="cens@t.local", name="cens", role="student", control_arm="closed"))
        db.add(Lab(slug="lan-static-ip", title="L1 Static IP", meta={"skill": _SKILL}))
        db.add(LabProgress(
            id="lp-cens-l1", user_id="cens-u1", lab_slug="lan-static-ip",
            status="completed", started_at=l1_start, completed_at=l1_end,
        ))
        db.add(LearningSession(
            id="sess-cens-l1", user_id="cens-u1", lab_slug="lan-static-ip",
            status="ended", started_at=l1_start, ended_at=l1_end,
        ))
        db.add(ExperimentMetrics(
            id="em-cens-l1", session_id="sess-cens-l1", user_id="cens-u1", lab_slug="lan-static-ip",
            experiment_group="closed", base_arm="closed",
            total_time_seconds=432000.0, steps_completed=3, total_errors=3, repeated_errors=2,
            unique_error_types=2, interventions_received=2, interventions_succeeded=0,
            interventions_failed=1, interventions_accepted=1, escalations=1,
            l2_unassisted_pass=None, final_score=0.5, completed=True,
        ))
        await db.commit()

    async with session_factory() as db:
        yield db

    await engine.dispose()


async def test_compute_cohort_metrics_censored_learner(censored_db):
    from cohort.service import compute_cohort_metrics

    out = await compute_cohort_metrics(censored_db, horizon_seconds=30 * 86400.0, by_arm=False)

    assert out["headline_arm"] == "closed"
    assert out["by_arm"] is None

    skills = {c.skill: c for c in out["by_skill"]}
    assert _SKILL in skills

    cell = skills[_SKILL]
    assert cell.n == 1
    assert cell.time_to_competence.reach_rate == 0.0
    assert cell.time_to_competence.censored == 1
    assert cell.time_to_competence.median_calendar_seconds is None
    assert cell.time_to_competence.reach_rate_at_horizon == 0.0


async def test_compute_cohort_metrics_one_learner(cohort_db):
    from cohort.service import compute_cohort_metrics

    out = await compute_cohort_metrics(cohort_db, horizon_seconds=30 * 86400.0, by_arm=True)

    assert out["headline_arm"] == "closed"

    skills = {c.skill: c for c in out["by_skill"]}
    assert _SKILL in skills

    cell = skills[_SKILL]
    assert cell.n == 1
    assert cell.time_to_competence.reach_rate == 1.0           # дошёл до L2
    assert cell.time_to_competence.median_calendar_seconds is not None

    assert out["by_arm"] is not None
    arms = {c.arm for c in out["by_arm"]}
    assert "closed" in arms
