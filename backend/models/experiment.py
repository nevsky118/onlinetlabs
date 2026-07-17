"""Метрики эксперимента."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ExperimentMetrics(Base):
    """Итоговые метрики сессии для статистического анализа."""

    __tablename__ = "experiment_metrics"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255))
    experiment_group: Mapped[str] = mapped_column(String(20))
    agent_backend: Mapped[str | None] = mapped_column(String(50), default=None)
    total_time_seconds: Mapped[float] = mapped_column(Float)
    steps_completed: Mapped[int] = mapped_column(Integer)
    total_errors: Mapped[int] = mapped_column(Integer)
    repeated_errors: Mapped[int] = mapped_column(Integer)
    unique_error_types: Mapped[int] = mapped_column(Integer)
    interventions_received: Mapped[int] = mapped_column(Integer, default=0)
    interventions_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    interventions_failed: Mapped[int] = mapped_column(Integer, default=0)
    interventions_accepted: Mapped[int] = mapped_column(Integer, default=0)
    # Task 8: расширенные метрики эксперимента
    control_arm: Mapped[str | None] = mapped_column(String(20), default=None)
    # base_arm = постоянный training-arm пользователя (User.control_arm); control_arm = effective arm сессии
    base_arm: Mapped[str | None] = mapped_column(String(20), default=None)
    escalations: Mapped[int] = mapped_column(Integer, default=0)
    would_interventions: Mapped[int] = mapped_column(Integer, default=0)
    l1_interventions: Mapped[int] = mapped_column(Integer, default=0)
    l2_unassisted_pass: Mapped[bool | None] = mapped_column(Boolean, default=None)
    final_score: Mapped[float] = mapped_column(Float)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
