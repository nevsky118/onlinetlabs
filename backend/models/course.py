from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.lab import Lab


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
