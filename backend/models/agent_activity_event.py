"""ORM row for an agent activity event."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class AgentActivityEventRow(Base):
    """An AI agent activity event (chat/interventions) for instructor observation."""

    __tablename__ = "agent_activity_events"
    __table_args__ = (Index("ix_agent_activity_session_ts", "session_id", "ts"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[str] = mapped_column(String(255))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    source: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(40))
    agent: Mapped[str | None] = mapped_column(String(40), default=None)
    severity: Mapped[str] = mapped_column(String(10), default="info")
    summary: Mapped[str] = mapped_column(Text)
    detail: Mapped[dict | None] = mapped_column(JSON, default=None)
