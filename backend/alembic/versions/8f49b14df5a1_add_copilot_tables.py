"""add copilot tables

Revision ID: 8f49b14df5a1
Revises: 7e28b03de3c8
Create Date: 2026-08-11 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8f49b14df5a1'
down_revision = '7e28b03de3c8'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('copilot_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_copilot_conversations_id'), 'copilot_conversations', ['id'], unique=False)
    
    op.create_table('copilot_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('tool_calls', sa.JSON(), nullable=True),
        sa.Column('structured_response', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['copilot_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_copilot_messages_id'), 'copilot_messages', ['id'], unique=False)
    op.create_index(op.f('ix_copilot_messages_role'), 'copilot_messages', ['role'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_copilot_messages_role'), table_name='copilot_messages')
    op.drop_index(op.f('ix_copilot_messages_id'), table_name='copilot_messages')
    op.drop_table('copilot_messages')
    op.drop_index(op.f('ix_copilot_conversations_id'), table_name='copilot_conversations')
    op.drop_table('copilot_conversations')
