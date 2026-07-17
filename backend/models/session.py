from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class LearningSession(Base):
    """A user's learning session in a lab with its status and timing."""

    __tablename__ = "learning_sessions"
    __table_args__ = (
        Index("ix_learning_sessions_user_status", "user_id", "status"),
        Index("ix_learning_sessions_user_started", "user_id", "started_at"),
        Index("ix_learning_sessions_user_lab_status", "user_id", "lab_slug", "status"),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255), ForeignKey("labs.slug", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(50), default="active")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict | None] = mapped_column(JSON, default=None)
    model_id: Mapped[str | None] = mapped_column(String(255), default=None)
