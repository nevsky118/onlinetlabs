from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class PlatformEvent(Base):
    """A named platform event tied to a user, session, and device."""

    __tablename__ = "platform_events"
    __table_args__ = (
        Index("ix_platform_events_user_ts", "user_id", "server_ts"),
        Index("ix_platform_events_session", "session_id"),
        Index("ix_platform_events_device_ts", "device_id", "server_ts"),
        Index("ix_platform_events_name_ts", "event_name", "server_ts"),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    event_name: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="SET NULL"), nullable=True
    )
    device_id: Mapped[str] = mapped_column(String(100))
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: {})
    client_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    server_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
