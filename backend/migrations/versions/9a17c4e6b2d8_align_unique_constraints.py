"""align research_id and pseudonym uniqueness with the models

Revision ID: 9a17c4e6b2d8
Revises: 5b8e3f1d0c47
Create Date: 2026-08-29 15:30:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = '9a17c4e6b2d8'
down_revision: Union[str, None] = '5b8e3f1d0c47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 7c4d2e9a6b18 named this constraint by hand while the model asks for the
    # default name, so autogenerate saw drift on every run.
    op.drop_constraint("uq_learning_sessions_research_id", "learning_sessions", type_="unique")
    op.create_unique_constraint(
        "learning_sessions_research_id_key", "learning_sessions", ["research_id"]
    )

    # 8f2a6d3c1b74 created a unique constraint and a separate non-unique index on
    # the same column. One unique index is what the model declares and all that is
    # needed: a unique constraint already builds one.
    op.drop_constraint("study_participants_pseudonym_key", "study_participants", type_="unique")
    op.drop_index("ix_study_participants_pseudonym", table_name="study_participants")
    op.create_index(
        "ix_study_participants_pseudonym", "study_participants", ["pseudonym"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_study_participants_pseudonym", table_name="study_participants")
    op.create_index("ix_study_participants_pseudonym", "study_participants", ["pseudonym"])
    op.create_unique_constraint(
        "study_participants_pseudonym_key", "study_participants", ["pseudonym"]
    )
    op.drop_constraint("learning_sessions_research_id_key", "learning_sessions", type_="unique")
    op.create_unique_constraint(
        "uq_learning_sessions_research_id", "learning_sessions", ["research_id"]
    )
