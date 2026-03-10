"""Инструменты AnalyticsAgent для анализа прогресса."""

from collections import Counter, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from agents.analytics.models import StudentMetrics


class AnalyticsTools:
    """Инструменты для аналитики прогресса студента."""

    def __init__(self, db: AsyncSession | None):
        self._db = db

    async def get_attempts(self, user_id: str, lab_slug: str) -> list:
        """Получить все StepAttempt для студента по лабе."""
        from sqlalchemy import select
        from models.progress import StepAttempt

        stmt = (
            select(StepAttempt)
            .where(StepAttempt.user_id == user_id, StepAttempt.lab_slug == lab_slug)
            .order_by(StepAttempt.started_at)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_lab_progress(self, user_id: str, lab_slug: str):
        """Получить LabProgress."""
        from sqlalchemy import select
        from models.progress import LabProgress

        stmt = select(LabProgress).where(
            LabProgress.user_id == user_id, LabProgress.lab_slug == lab_slug
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    def compute_metrics(self, attempts: list) -> StudentMetrics:
        """Вычислить метрики из списка StepAttempt."""
        if not attempts:
            return StudentMetrics(
                total_attempts=0,
                success_rate=0.0,
                avg_time_per_step=0.0,
                struggling_steps=[],
            )

        total = len(attempts)
        successes = sum(1 for a in attempts if a.result == "pass")
        success_rate = successes / total

        # Среднее время
        times = []
        for a in attempts:
            if a.started_at and a.ended_at:
                delta = (a.ended_at - a.started_at).total_seconds()
                times.append(delta)
        avg_time = sum(times) / len(times) if times else 0.0

        # Struggling steps: >2 последовательных неудач на одном шаге
        consecutive_fails: dict[str, int] = defaultdict(int)
        max_consecutive: dict[str, int] = defaultdict(int)

        for a in attempts:
            if a.result != "pass":
                consecutive_fails[a.step_slug] += 1
                max_consecutive[a.step_slug] = max(
                    max_consecutive[a.step_slug], consecutive_fails[a.step_slug]
                )
            else:
                consecutive_fails[a.step_slug] = 0

        struggling = [s for s, c in max_consecutive.items() if c > 2]

        return StudentMetrics(
            total_attempts=total,
            success_rate=round(success_rate, 4),
            avg_time_per_step=round(avg_time, 2),
            struggling_steps=struggling,
        )

    def detect_error_patterns(self, attempts: list) -> list[str]:
        """Найти повторяющиеся паттерны ошибок (>= 2 повторений)."""
        errors = [
            a.error_details
            for a in attempts
            if a.error_details is not None
        ]
        counts = Counter(errors)
        return [err for err, count in counts.items() if count >= 2]
