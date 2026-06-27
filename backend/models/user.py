"""Совместимая с Auth.js схема для OAuth-провайдеров, например GitHub."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class UserRole(str, Enum):
    """Роли пользователя для разграничения доступа."""

    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class User(Base):
    """Таблица users Auth.js."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
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
    default_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=False)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Account(Base):
    """Таблица accounts Auth.js. Хранит данные OAuth-провайдеров."""

    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE")
    )
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

    user: Mapped["User"] = relationship(back_populates="accounts")


class Session(Base):
    """Таблица sessions Auth.js."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    session_token: Mapped[str] = mapped_column(String(255), unique=True)
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE")
    )
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions")


class VerificationToken(Base):
    """Verification-токены Auth.js для подтверждения email."""

    __tablename__ = "verification_tokens"

    identifier: Mapped[str] = mapped_column(String(255), primary_key=True)
    token: Mapped[str] = mapped_column(String(255), primary_key=True)
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))
