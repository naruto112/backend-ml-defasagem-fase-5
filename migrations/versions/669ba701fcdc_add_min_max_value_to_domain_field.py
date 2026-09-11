"""add_min_max_value_to_domain_field

Revision ID: 669ba701fcdc
Revises: 0c2e38a2b548
Create Date: 2026-09-10 23:08:18.910565
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '669ba701fcdc'
down_revision: Union[str, None] = '0c2e38a2b548'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('domain_field', sa.Column('min_value', sa.Float(), nullable=True))
    op.add_column('domain_field', sa.Column('max_value', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('domain_field', 'max_value')
    op.drop_column('domain_field', 'min_value')
