from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class SessionEvidenceSnapshot(Base):
    """Сырое свидетельство сессии для слепой человеческой разметки.

    Реплеябельный поток (упорядочен по ts), DISJOINT от 16 признаков и от правил:
    разметчик кодирует режим из сырья (MCP-наблюдения / топология / консоль), а не
    из вектора признаков — иначе тавтология F1=1.0 возвращается. kind — вид свидетельства.
    """

    __tablename__ = "session_evidence_snapshots"
    __table_args__ = (
        Index("ix_session_evidence_snapshots_session_ts", "session_id", "ts"),
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
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    kind: Mapped[str] = mapped_column(String(50))  # mcp_events | topology | console | ...
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
