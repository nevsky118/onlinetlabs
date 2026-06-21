"""Согласие обучаемого: study (эксперимент) и product (гранулярно observe/act)."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    scope: Mapped[str] = mapped_column(String(20))             # study | product
    observe: Mapped[bool] = mapped_column(Boolean, default=False)
    act: Mapped[bool] = mapped_column(Boolean, default=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    data_policy: Mapped[str | None] = mapped_column(String(255), default=None)
