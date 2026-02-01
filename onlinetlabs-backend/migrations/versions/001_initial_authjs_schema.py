"""Initial Auth.js schema

Revision ID: 001
Revises:
Create Date: 2024-01-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("email_verified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("image", sa.Text(), nullable=True),
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(255), nullable=False),
        sa.Column("provider_account_id", sa.String(255), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.Integer(), nullable=True),
        sa.Column("token_type", sa.String(255), nullable=True),
        sa.Column("scope", sa.String(255), nullable=True),
        sa.Column("id_token", sa.Text(), nullable=True),
        sa.Column("session_state", sa.String(255), nullable=True),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("session_token", sa.String(255), unique=True, nullable=False),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "verification_tokens",
        sa.Column("identifier", sa.String(255), primary_key=True),
        sa.Column("token", sa.String(255), primary_key=True),
        sa.Column("expires", sa.DateTime(timezone=True), nullable=False),
    )

    # Indexes for common queries
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_sessions_user_id", "sessions")
    op.drop_index("ix_accounts_user_id", "accounts")
    op.drop_table("verification_tokens")
    op.drop_table("sessions")
    op.drop_table("accounts")
    op.drop_table("users")
