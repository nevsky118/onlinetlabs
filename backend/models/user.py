"""Auth.js-compatible schema for OAuth providers, e.g. GitHub."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class UserRole(str, Enum):
    """User roles for access control."""

    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class User(Base):
    """Auth.js users table."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    email_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    image: Mapped[str | None] = mapped_column(Text)
    password_hash: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.STUDENT.value)
    experiment_group: Mapped[str | None] = mapped_column(String(20), default=None)
    control_arm: Mapped[str | None] = mapped_column(String(20), default=None)
    can_select_model: Mapped[bool | None] = mapped_column(default=None)
    can_view_agent_logs: Mapped[bool | None] = mapped_column(default=None)
    # Firewall: a simulated student; excluded from "real results"
    is_simulated: Mapped[bool] = mapped_column(default=False)
    default_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=False
    )

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="raise"
    )
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="raise"
    )


class Account(Base):
    """Auth.js accounts table. Stores OAuth provider data."""

    __tablename__ = "accounts"
    __table_args__ = (Index("ix_accounts_user_id", "user_id"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(255))  # oauth, email, credentials
    provider: Mapped[str] = mapped_column(String(255))  # github, google, etc
    provider_account_id: Mapped[str] = mapped_column(String(255))
    refresh_token: Mapped[str | None] = mapped_column(Text)
    access_token: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[int | None] = mapped_column(Integer)
    token_type: Mapped[str | None] = mapped_column(String(255))
    scope: Mapped[str | None] = mapped_column(String(255))
    id_token: Mapped[str | None] = mapped_column(Text)
    session_state: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="accounts", lazy="raise")


class Session(Base):
    """Auth.js sessions table."""

    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_user_id", "user_id"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_token: Mapped[str] = mapped_column(String(255), unique=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions", lazy="raise")


class VerificationToken(Base):
    """Auth.js verification tokens for email confirmation."""

    __tablename__ = "verification_tokens"

    identifier: Mapped[str] = mapped_column(String(255), primary_key=True)
    token: Mapped[str] = mapped_column(String(255), primary_key=True)
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))
