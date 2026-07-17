from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class InterventionDecision(Base):
    """An MRT decision point: eligible moment + randomized assignment + spell outcome.

    Direct input to the hazard model (P4). An unconfounded intervene/withhold contrast
    over the dwell range is recovered by grouping on spell_id.
    """

    __tablename__ = "intervention_decisions"
    __table_args__ = (
        Index("ix_intervention_decisions_session_ts", "session_id", "ts"),
        Index("ix_intervention_decisions_spell", "spell_id"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE")
    )
    lab_slug: Mapped[str] = mapped_column(String(255))
    spell_id: Mapped[str] = mapped_column(String(255))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    regime: Mapped[str] = mapped_column(String(50))
    dwell_seconds: Mapped[float] = mapped_column(Float)
    t_k_applied: Mapped[float] = mapped_column(Float)
    assignment: Mapped[str] = mapped_column(String(20))  # "intervene" | "withhold"
    subsequent_exit_ts: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    censored: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
