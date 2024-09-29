"""Add created_at and is_active fields

Revision ID: f22b10ac170e
Revises: 
Create Date: 2024-09-26 22:32:16.450800

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f22b10ac170e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_input', sa.Text(), nullable=False),
    sa.Column('ai_response', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_chat_id', sa.Integer(), nullable=True),
    sa.Column('ai_chat_id', sa.Integer(), nullable=True),
    sa.Column('emoji', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['ai_chat_id'], ['chat_log.id'], ),
    sa.ForeignKeyConstraint(['user_chat_id'], ['chat_log.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('reaction')
    op.drop_table('chat_log')
    # ### end Alembic commands ###
