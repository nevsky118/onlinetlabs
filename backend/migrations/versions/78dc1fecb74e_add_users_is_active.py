"""add users.is_active column

Revision ID: 78dc1fecb74e
Revises: 310618cd8071
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa

revision = "78dc1fecb74e"
down_revision = "310618cd8071"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("users", "is_active")
