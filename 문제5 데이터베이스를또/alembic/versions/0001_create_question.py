# alembic/versions/0001_create_question.py
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_question'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'question',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('create_date', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_question_id', 'question', ['id'], unique=False)
    op.create_index('ix_question_subject', 'question', ['subject'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_question_subject', table_name='question')
    op.drop_index('ix_question_id', table_name='question')
    op.drop_table('question')
