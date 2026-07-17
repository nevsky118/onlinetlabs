from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class GroundingComparison(Base):
    """A pair of help variants (with live MCP context vs. task text only).

    For blind expert evaluation: isolates the single novelty of "grounding in
    live environment state" with a metric that can't be computed from the rules.
    """

    __tablename__ = "grounding_comparisons"
    __table_args__ = (
        Index("ix_grounding_comparisons_session", "session_id"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    grounded_text: Mapped[str] = mapped_column(Text)
    ungrounded_text: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
