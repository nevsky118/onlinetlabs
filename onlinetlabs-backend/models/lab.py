from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.course import Course


class Lab(Base):
    __tablename__ = "labs"

    slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(50), default="beginner")
    course_slug: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("courses.slug", ondelete="SET NULL"), nullable=True
    )
    order_in_course: Mapped[int] = mapped_column(Integer, default=0)
    environment_type: Mapped[str] = mapped_column(String(50), default="none")
    meta: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    course: Mapped["Course | None"] = relationship(back_populates="labs")
    steps: Mapped[list["LabStep"]] = relationship(
        back_populates="lab",
        cascade="all, delete-orphan",
        order_by="LabStep.step_order",
    )


class LabStep(Base):
    __tablename__ = "lab_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lab_slug: Mapped[str] = mapped_column(
        String(255), ForeignKey("labs.slug", ondelete="CASCADE")
    )
    step_order: Mapped[int] = mapped_column(Integer)
    slug: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    validation_type: Mapped[str | None] = mapped_column(String(100))

    lab: Mapped["Lab"] = relationship(back_populates="steps")
