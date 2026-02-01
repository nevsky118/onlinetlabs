"""add_password_hash_and_role

Revision ID: a71aa2584864
Revises: 001
Create Date: 2026-02-18 16:54:15.041500
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a71aa2584864"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "role", sa.String(length=50), server_default="student", nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
