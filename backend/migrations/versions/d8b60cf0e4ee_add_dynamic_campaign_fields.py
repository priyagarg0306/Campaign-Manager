"""Add dynamic campaign fields

Revision ID: d8b60cf0e4ee
Revises: c7a59cf9f3dd
Create Date: 2026-01-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8b60cf0e4ee'
down_revision = 'c7a59cf9f3dd'
branch_labels = None
depends_on = None


def upgrade():
    # Add bidding strategy fields
    with op.batch_alter_table('campaigns', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bidding_strategy', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('target_cpa', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('target_roas', sa.Float(), nullable=True))

    # Add new dynamic campaign fields
    with op.batch_alter_table('campaigns', schema=None) as batch_op:
        batch_op.add_column(sa.Column('headlines', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('long_headline', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('descriptions', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('business_name', sa.String(length=25), nullable=True))
        batch_op.add_column(sa.Column('images', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('keywords', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('video_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('merchant_center_id', sa.String(length=100), nullable=True))


def downgrade():
    # Remove new dynamic campaign fields
    with op.batch_alter_table('campaigns', schema=None) as batch_op:
        batch_op.drop_column('merchant_center_id')
        batch_op.drop_column('video_url')
        batch_op.drop_column('keywords')
        batch_op.drop_column('images')
        batch_op.drop_column('business_name')
        batch_op.drop_column('descriptions')
        batch_op.drop_column('long_headline')
        batch_op.drop_column('headlines')

    # Remove bidding strategy fields
    with op.batch_alter_table('campaigns', schema=None) as batch_op:
        batch_op.drop_column('target_roas')
        batch_op.drop_column('target_cpa')
        batch_op.drop_column('bidding_strategy')
