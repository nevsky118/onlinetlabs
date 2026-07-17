"""Latency instrumentation: cycle stage percentiles (p50/p95/p99, not mean)."""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from evaluation.stats import percentile
from models.cycle_latency_sample import CycleLatencySample


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
    db.add(CycleLatencySample(
        session_id=session_id, stage=stage, duration_ms=duration_ms,
        ts=datetime.now(tz=UTC),
    ))
    await db.commit()


async def stage_percentiles(
    db: AsyncSession, stage: str, ps: list[int]
) -> dict[int, float]:
    """p50/p95/p99 stage latency across all recorded samples."""
    rows = (await db.execute(
        select(CycleLatencySample.duration_ms).where(CycleLatencySample.stage == stage)
    )).scalars().all()
    return percentiles(list(rows), ps)
