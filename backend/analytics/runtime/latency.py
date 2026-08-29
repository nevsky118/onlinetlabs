"""Latency instrumentation: cycle stage percentiles (p50/p95/p99, not mean)."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import array as pg_array
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.metrics.stats import percentile
from models.research import CycleLatencySample


def percentiles(values: list[float], ps: list[int]) -> dict[int, float]:
    """Percentiles under one convention (Hyndman-Fan Type 7). Empty input → zeros.

    Mean hides the tail; the reviewer requires p50/p95/p99 under load.
    """
    if not values:
        return dict.fromkeys(ps, 0.0)
    return {p: percentile(values, p) for p in ps}


async def record_stage_latency(
    db: AsyncSession, session_id: str, stage: str, duration_ms: float
) -> None:
    """Record the latency of one cycle stage."""
    db.add(
        CycleLatencySample(
            session_id=session_id,
            stage=stage,
            duration_ms=duration_ms,
            ts=datetime.now(tz=UTC),
        )
    )
    await db.commit()


async def stage_percentiles(db: AsyncSession, stage: str, ps: list[int]) -> dict[int, float]:
    """p50/p95/p99 stage latency, computed by the database where it can."""
    if not ps:
        return {}
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        # a plain list binds as one scalar parameter; percentile_cont needs an array
        fractions = pg_array([p / 100 for p in ps])
        row = (
            await db.execute(
                select(
                    func.percentile_cont(fractions).within_group(
                        CycleLatencySample.duration_ms.asc()
                    )
                ).where(CycleLatencySample.stage == stage)
            )
        ).scalar_one_or_none()
        if not row:
            return dict.fromkeys(ps, 0.0)
        return {p: float(value) for p, value in zip(ps, row, strict=False)}

    # sqlite has no percentile_cont; the test harness runs on it
    rows = (
        (
            await db.execute(
                select(CycleLatencySample.duration_ms).where(CycleLatencySample.stage == stage)
            )
        )
        .scalars()
        .all()
    )
    return percentiles(list(rows), ps)
