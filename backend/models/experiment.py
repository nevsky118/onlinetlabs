"""Метрики эксперимента."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ExperimentMetrics(Base):
    """Итоговые метрики сессии для статистического анализа."""

    __tablename__ = "experiment_metrics"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE")
    )
    lab_slug: Mapped[str] = mapped_column(String(255))
    experiment_group: Mapped[str] = mapped_column(String(20))
    total_time_seconds: Mapped[float] = mapped_column(Float)
    steps_completed: Mapped[int] = mapped_column(Integer)
    total_errors: Mapped[int] = mapped_column(Integer)
    repeated_errors: Mapped[int] = mapped_column(Integer)
    unique_error_types: Mapped[int] = mapped_column(Integer)
    interventions_received: Mapped[int] = mapped_column(Integer, default=0)
    interventions_accepted: Mapped[int] = mapped_column(Integer, default=0)
    final_score: Mapped[float] = mapped_column(Float)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
