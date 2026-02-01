"""Auth.js compatible schema for OAuth providers like GitHub."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
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

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    email_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    image: Mapped[str | None] = mapped_column(Text)
    password_hash: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.STUDENT.value)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Account(Base):
    """Auth.js accounts table - stores OAuth provider data."""

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
    """Auth.js sessions table."""

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
    """Auth.js verification tokens for email verification."""

    __tablename__ = "verification_tokens"

    identifier: Mapped[str] = mapped_column(String(255), primary_key=True)
    token: Mapped[str] = mapped_column(String(255), primary_key=True)
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))
