from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ValidationRun(Base):
    """A lab check run within a session with its status and per-step results."""

    __tablename__ = "validation_runs"
    __table_args__ = (
        Index(
            "validation_runs_session_idx",
            "session_id",
            text("started_at DESC"),
        ),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("learning_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    lab_slug: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    # JSONB in Postgres; plain JSON elsewhere so the SQLite unit-test harness can compile it.
    steps: Mapped[list] = mapped_column(
        sa.JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("now()"),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
