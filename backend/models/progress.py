from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class CourseProgress(Base):
    __tablename__ = "course_progress"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "course_slug", name="uq_course_progress_user_course"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE")
    )
    course_slug: Mapped[str] = mapped_column(
        String(255), ForeignKey("courses.slug", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(50), default="not_started")
    score: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class LabProgress(Base):
    __tablename__ = "lab_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lab_slug", name="uq_lab_progress_user_lab"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE")
    )
    lab_slug: Mapped[str] = mapped_column(
        String(255), ForeignKey("labs.slug", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(50), default="not_started")
    score: Mapped[float | None] = mapped_column(Float)
    current_step: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class StepAttempt(Base):
    __tablename__ = "step_attempts"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE")
    )
    lab_slug: Mapped[str] = mapped_column(
        String(255), ForeignKey("labs.slug", ondelete="CASCADE")
    )
    step_slug: Mapped[str] = mapped_column(String(255))
    attempt_number: Mapped[int] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(50))
    score: Mapped[float | None] = mapped_column(Float)
    error_details: Mapped[dict | None] = mapped_column(JSON, default=None)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
