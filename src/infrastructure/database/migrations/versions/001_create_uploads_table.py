"""empty message

Revision ID: 001
Revises: 
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa


revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'uploads',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('s3_key', sa.String(500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='RECEIVED'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(),
                  onupdate=sa.func.now()),
    )
    op.create_index('ix_uploads_status', 'uploads', ['status'])


def downgrade() -> None:
    op.drop_index('ix_uploads_status', 'uploads')
    op.drop_table('uploads')
