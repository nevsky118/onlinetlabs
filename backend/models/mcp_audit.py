"""Append-only лог вызовов через контур (observe/act). Act-записи = источник воздействий для J/cohort."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class MCPAudit(Base):
    __tablename__ = "mcp_audit"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    tool: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(20))  # observe | act
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    success: Mapped[bool] = mapped_column(Boolean)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    consent_ref: Mapped[str | None] = mapped_column(String(36), default=None)
    lab_slug: Mapped[str | None] = mapped_column(String(255), default=None)
