from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class BehavioralEvent(Base):
    __tablename__ = "behavioral_events"
    __table_args__ = (
        Index("ix_behavioral_events_session_ts", "session_id", "timestamp"),
        Index("ix_behavioral_events_user_lab", "user_id", "lab_slug"),
        Index("ix_behavioral_events_session_type", "session_id", "event_type"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE")
    )
    lab_slug: Mapped[str] = mapped_column(
        String(255), ForeignKey("labs.slug", ondelete="CASCADE")
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_type: Mapped[str] = mapped_column(String(50))
    component_id: Mapped[str | None] = mapped_column(String(255))
    component_type: Mapped[str | None] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(255))
    raw_command: Mapped[str | None] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean)
    severity: Mapped[str | None] = mapped_column(String(50))
    message: Mapped[str | None] = mapped_column(Text)
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
