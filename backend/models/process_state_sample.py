from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ProcessStateSample(Base):
    """Снимок состояния управляемого процесса (time-series)."""

    __tablename__ = "process_state_samples"
    __table_args__ = (Index("ix_process_state_samples_session_ts", "session_id", "ts"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    regime: Mapped[str] = mapped_column(String(50))
    dwell_seconds: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
