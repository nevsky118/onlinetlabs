"""add mcp_audit table

Revision ID: 007_mcp_audit
Revises: 006_consent
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = "007_mcp_audit"
down_revision = "006_consent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mcp_audit",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("session_id", sa.String(255), nullable=False, index=True),
        sa.Column("tool", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("consent_ref", sa.String(36), nullable=True),
        sa.Column("lab_slug", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("mcp_audit")
