"""Append-only records: tool calls, platform events, consent."""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class MCPAudit(Base):
    __tablename__ = "mcp_audit"
    __table_args__ = (Index("ix_mcp_audit_ts", "ts"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    tool: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(20))  # observe | act
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    success: Mapped[bool] = mapped_column(Boolean)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    consent_ref: Mapped[str | None] = mapped_column(String(36), default=None)
    lab_slug: Mapped[str | None] = mapped_column(String(255), default=None)


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
    # JSONB in Postgres; plain JSON elsewhere so the SQLite unit-test harness can compile it.
    properties: Mapped[dict] = mapped_column(
        sa.JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=lambda: {}
    )
    client_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    server_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )


class AgentActivityEventRow(Base):
    """An AI agent activity event (chat/interventions) for instructor observation."""

    __tablename__ = "agent_activity_events"
    __table_args__ = (Index("ix_agent_activity_session_ts", "session_id", "ts"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[str] = mapped_column(String(255))
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    source: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(40))
    agent: Mapped[str | None] = mapped_column(String(40), default=None)
    severity: Mapped[str] = mapped_column(String(10), default="info")
    summary: Mapped[str] = mapped_column(Text)
    detail: Mapped[dict | None] = mapped_column(JSON, default=None)


class Consent(Base):
    __tablename__ = "consents"
    __table_args__ = (Index("ix_consents_user_scope", "user_id", "scope"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    scope: Mapped[str] = mapped_column(String(20))  # study | product
    decision: Mapped[str] = mapped_column(String(20), default="granted")
    policy_version: Mapped[str] = mapped_column(String(20), default="1")
    observe: Mapped[bool] = mapped_column(Boolean, default=False)
    act: Mapped[bool] = mapped_column(Boolean, default=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    data_policy: Mapped[str | None] = mapped_column(String(255), default=None)
