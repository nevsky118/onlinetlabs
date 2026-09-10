import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gns3_user_id: Mapped[str] = mapped_column(String(64))
    gns3_username: Mapped[str] = mapped_column(String(128))
    # The GNS3 account password is not stored in the DB: it's owned by the GNS3
    # server, and for internal needs a JWT issued by the admin client is enough.
    gns3_project_id: Mapped[str] = mapped_column(String(64))
    student_user_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), insert_default=SessionStatus.ACTIVE
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    events: Mapped[list["HistoryEvent"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("status", SessionStatus.ACTIVE)
        super().__init__(**kwargs)


class HistoryEvent(Base):
    __tablename__ = "history_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(128))
    component_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    session: Mapped["Session"] = relationship(back_populates="events")


class ConsoleChunk(Base):
    """One raw frame of a node console, as it crossed the proxy.

    `in` is what the learner typed, `out` what the node answered. Frame
    boundaries carry no meaning, so nothing is parsed here; ConsoleCommand rows
    are derived from these, which lets a changed parser be re-run.
    """

    __tablename__ = "console_chunks"
    __table_args__ = (
        # Replay orders by seq: timestamps within a millisecond collide.
        Index("ix_console_chunks_connection_seq", "connection_id", "seq"),
        Index("ix_console_chunks_session_ts", "session_id", "ts"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"), index=True)
    node_id: Mapped[str] = mapped_column(String(64))
    # One console socket; a session has many.
    connection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    seq: Mapped[int] = mapped_column(BigInteger)
    direction: Mapped[str] = mapped_column(String(3))  # in | out
    payload: Mapped[bytes] = mapped_column(LargeBinary)
    truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    # Masked before storing: a password prompt was open.
    redacted: Mapped[bool] = mapped_column(Boolean, default=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ConsoleCommand(Base):
    """One command a learner ran on a node console, with the node's answer.

    Derived from the console stream, never captured directly; the raw chunks
    stay the source of truth.
    """

    __tablename__ = "console_commands"
    __table_args__ = (
        Index("ix_console_commands_session_ts", "session_id", "ts"),
        Index("ix_console_commands_connection_seq", "connection_id", "seq"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"), index=True)
    node_id: Mapped[str] = mapped_column(String(64))
    connection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    seq: Mapped[int] = mapped_column(BigInteger)
    # Carries the device mode: "R1(config-if)#" means configuring an interface.
    prompt: Mapped[str | None] = mapped_column(String(255))
    command: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Echo to next prompt: the device's think time, not the learner's.
    duration_ms: Mapped[float | None] = mapped_column(Float)
