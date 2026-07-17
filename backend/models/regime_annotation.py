from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class RegimeAnnotation(Base):
    """Разметка режима коллаборантом по окну сессии (для IRR / kappa и adjudicated gold).

    coder_id — разметчик, НЕ автор правил (иначе тавтология). window_index выравнивает
    метки разных коллаборантов для Cohen's kappa. is_gold — adjudicated-эталон.
    """

    __tablename__ = "regime_annotations"
    __table_args__ = (
        Index("ix_regime_annotations_session_window", "session_id", "window_index"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    coder_id: Mapped[str] = mapped_column(String(255))
    window_index: Mapped[int] = mapped_column(Integer)
    regime_label: Mapped[str] = mapped_column(String(50))
    is_gold: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
