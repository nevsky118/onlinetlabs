"""sort indexes for every table the admin browser lists

Revision ID: 3d6a91c7e04b
Revises: 9a17c4e6b2d8
Create Date: 2026-08-29 14:48:08.353060
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '3d6a91c7e04b'
down_revision: Union[str, None] = '9a17c4e6b2d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            op.f('ix_agent_activity_events_ts'), 'agent_activity_events', ['ts'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_behavioral_events_timestamp'), 'behavioral_events', ['timestamp'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_chat_messages_created_at'), 'chat_messages', ['created_at'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_consents_granted_at'), 'consents', ['granted_at'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_course_progress_updated_at'), 'course_progress', ['updated_at'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_cycle_latency_samples_ts'), 'cycle_latency_samples', ['ts'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_experiment_metrics_created_at'), 'experiment_metrics', ['created_at'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_grounding_comparisons_ts'), 'grounding_comparisons', ['ts'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_intervention_decisions_ts'), 'intervention_decisions', ['ts'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_intervention_decisions_user_id'), 'intervention_decisions', ['user_id'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_lab_progress_updated_at'), 'lab_progress', ['updated_at'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_learning_sessions_started_at'), 'learning_sessions', ['started_at'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_platform_events_server_ts'), 'platform_events', ['server_ts'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_process_state_samples_ts'), 'process_state_samples', ['ts'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_regime_annotations_created_at'), 'regime_annotations', ['created_at'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_session_evidence_snapshots_ts'), 'session_evidence_snapshots', ['ts'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_step_attempts_started_at'), 'step_attempts', ['started_at'], unique=False, postgresql_concurrently=True
        )
        op.create_index(
            op.f('ix_validation_runs_started_at'), 'validation_runs', ['started_at'], unique=False, postgresql_concurrently=True
        )
    

def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            op.f('ix_validation_runs_started_at'), table_name='validation_runs', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_step_attempts_started_at'), table_name='step_attempts', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_session_evidence_snapshots_ts'), table_name='session_evidence_snapshots', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_regime_annotations_created_at'), table_name='regime_annotations', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_process_state_samples_ts'), table_name='process_state_samples', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_platform_events_server_ts'), table_name='platform_events', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_learning_sessions_started_at'), table_name='learning_sessions', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_lab_progress_updated_at'), table_name='lab_progress', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_intervention_decisions_user_id'), table_name='intervention_decisions', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_intervention_decisions_ts'), table_name='intervention_decisions', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_grounding_comparisons_ts'), table_name='grounding_comparisons', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_experiment_metrics_created_at'), table_name='experiment_metrics', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_cycle_latency_samples_ts'), table_name='cycle_latency_samples', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_course_progress_updated_at'), table_name='course_progress', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_consents_granted_at'), table_name='consents', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_chat_messages_created_at'), table_name='chat_messages', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_behavioral_events_timestamp'), table_name='behavioral_events', postgresql_concurrently=True
        )
        op.drop_index(
            op.f('ix_agent_activity_events_ts'), table_name='agent_activity_events', postgresql_concurrently=True
        )
    