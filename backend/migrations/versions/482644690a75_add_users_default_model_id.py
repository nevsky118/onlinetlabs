"""add users.default_model_id column

Revision ID: 482644690a75
Revises: 310618cd8071
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa

revision = "482644690a75"
down_revision = "310618cd8071"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("default_model_id", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "default_model_id")
