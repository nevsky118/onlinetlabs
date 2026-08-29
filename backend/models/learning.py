"""What a learner does: sessions, progress, validation runs, chat."""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from i18n import Locale
from models.base import Base


class LearningSession(Base):
    """A user's learning session in a lab with its status and timing."""

    __tablename__ = "learning_sessions"
    __table_args__ = (
        Index("ix_learning_sessions_user_status", "user_id", "status"),
        Index("ix_learning_sessions_user_started", "user_id", "started_at"),
        Index("ix_learning_sessions_user_lab_status", "user_id", "lab_slug", "status"),
        Index("ix_learning_sessions_status_last_seen", "status", "last_seen_at"),
        Index("ix_learning_sessions_status_expires", "status", "expires_at"),
        Index(
            "uq_learning_sessions_one_live",
            "user_id",
            "lab_slug",
            unique=True,
            postgresql_where=text("status IN ('active', 'provisioning')"),
        ),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255), ForeignKey("labs.slug", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(50), default="active")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    research_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid4())
    )
    meta: Mapped[dict | None] = mapped_column(JSON, default=None)
    model_id: Mapped[str | None] = mapped_column(String(255), default=None)
    locale: Mapped[Locale] = mapped_column(
        String(5), nullable=False, server_default="en", default="en"
    )


class CourseProgress(Base):
    """User's progress on a course. Status, score, and timing."""

    __tablename__ = "course_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "course_slug", name="uq_course_progress_user_course"),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    course_slug: Mapped[str] = mapped_column(
        String(255), ForeignKey("courses.slug", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(50), default="not_started")
    score: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        index=True,
    )


class LabProgress(Base):
    """User's progress on a lab. Status, score, and current step."""

    __tablename__ = "lab_progress"
    __table_args__ = (UniqueConstraint("user_id", "lab_slug", name="uq_lab_progress_user_lab"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255), ForeignKey("labs.slug", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(50), default="not_started")
    score: Mapped[float | None] = mapped_column(Float)
    current_step: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        index=True,
    )


class StepAttempt(Base):
    """A lab step attempt with its number, result, and score."""

    __tablename__ = "step_attempts"
    __table_args__ = (
        Index("ix_step_attempts_user_lab_step", "user_id", "lab_slug", "step_slug"),
        UniqueConstraint(
            "user_id",
            "lab_slug",
            "step_slug",
            "attempt_number",
            name="uq_step_attempts_number",
        ),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255), ForeignKey("labs.slug", ondelete="CASCADE"))
    step_slug: Mapped[str] = mapped_column(String(255))
    attempt_number: Mapped[int] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(50))
    score: Mapped[float | None] = mapped_column(Float)
    error_details: Mapped[dict | None] = mapped_column(JSON, default=None)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


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
        index=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChatMessage(Base):
    """A chat message within a learning session with role, parts, and token usage."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    parts: Mapped[list] = mapped_column(JSON)
    usage: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
