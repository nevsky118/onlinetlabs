"""add consents table

Revision ID: 006_consent
Revises: 005_experiment_metrics_base_arm
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = "006_consent"
down_revision = "005_experiment_metrics_base_arm"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("observe", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("act", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_policy", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("consents")
