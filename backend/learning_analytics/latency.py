"""Latency-инструментовка: перцентили стадий цикла (p50/p95/p99, не среднее)."""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from evaluation.stats import percentile
from models.cycle_latency_sample import CycleLatencySample


def percentiles(values: list[float], ps: list[int]) -> dict[int, float]:
    """Перцентили по единой конвенции (Hyndman-Fan Type 7). Пустой вход → нули.

    Среднее скрывает хвост; рецензент требует p50/p95/p99 под нагрузкой.
    """
    if not values:
        return dict.fromkeys(ps, 0.0)
    return {p: percentile(values, p) for p in ps}


async def record_stage_latency(
    db: AsyncSession, session_id: str, stage: str, duration_ms: float
) -> None:
    """Записать латентность одной стадии цикла."""
    db.add(CycleLatencySample(
        session_id=session_id, stage=stage, duration_ms=duration_ms,
        ts=datetime.now(tz=UTC),
    ))
    await db.commit()


async def stage_percentiles(
    db: AsyncSession, stage: str, ps: list[int]
) -> dict[int, float]:
    """p50/p95/p99 латентности стадии по всем записанным сэмплам."""
    rows = (await db.execute(
        select(CycleLatencySample.duration_ms).where(CycleLatencySample.stage == stage)
    )).scalars().all()
    return percentiles(list(rows), ps)
