from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class CycleLatencySample(Base):
    """Latency of a single cycle stage (for p50/p95/p99 under load, not the mean)."""

    __tablename__ = "cycle_latency_samples"
    __table_args__ = (
        Index("ix_cycle_latency_samples_session_stage", "session_id", "stage"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    stage: Mapped[str] = mapped_column(String(50))  # analysis | mcp_context | llm | deliver
    duration_ms: Mapped[float] = mapped_column(Float)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
