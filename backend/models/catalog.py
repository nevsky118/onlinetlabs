"""Published content: courses, labs and their steps."""

from __future__ import annotations

from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Course(Base):
    """A course with a set of labs, difficulty, and prerequisites."""

    __tablename__ = "courses"

    slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    # JSONB in Postgres; plain JSON elsewhere so the SQLite unit-test harness can compile it.
    title_i18n: Mapped[dict] = mapped_column(
        sa.JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    description_i18n: Mapped[dict | None] = mapped_column(
        sa.JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    difficulty: Mapped[str] = mapped_column(String(50), default="beginner")
    order: Mapped[int] = mapped_column(Integer, default=0)
    prerequisites: Mapped[dict | None] = mapped_column(JSON, default=None)
    meta: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    labs: Mapped[list[Lab]] = relationship(back_populates="course", lazy="raise")


class Lab(Base):
    """A lab. Tied to a course, has an execution environment and steps."""

    __tablename__ = "labs"

    slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    # JSONB in Postgres; plain JSON elsewhere so the SQLite unit-test harness can compile it.
    title_i18n: Mapped[dict] = mapped_column(
        sa.JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    description_i18n: Mapped[dict | None] = mapped_column(
        sa.JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    difficulty: Mapped[str] = mapped_column(String(50), default="beginner")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    course_slug: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("courses.slug", ondelete="SET NULL"), nullable=True
    )
    order_in_course: Mapped[int] = mapped_column(Integer, default=0)
    environment_type: Mapped[str] = mapped_column(String(50), default="none")
    gns3_template_project_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gns3_template_project_id_iosvl2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gns3_template_project_id_frr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gns3_completed_template_project_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    meta: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    course: Mapped[Course | None] = relationship(back_populates="labs", lazy="raise")
    steps: Mapped[list[LabStep]] = relationship(
        back_populates="lab",
        cascade="all, delete-orphan",
        order_by="LabStep.step_order",
        lazy="raise",
    )


class LabStep(Base):
    """A lab step with its order and validation type."""

    __tablename__ = "lab_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lab_slug: Mapped[str] = mapped_column(String(255), ForeignKey("labs.slug", ondelete="CASCADE"))
    step_order: Mapped[int] = mapped_column(Integer)
    slug: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    validation_type: Mapped[str | None] = mapped_column(String(100))

    lab: Mapped[Lab] = relationship(back_populates="steps", lazy="raise")
