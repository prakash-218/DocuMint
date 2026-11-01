"""a purchase order's costing

Revision ID: 0018
Revises: 0017
Create Date: 2026-11-01 00:00:00

A purchase order made from a costing's lines keeps the costing and what those lines were costed at, so a job's profit
can set what is paid for them against what they were costed at. Going back drops both.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0018'
down_revision: Union[str, None] = '0017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('invoice', sa.Column('costing_id', sa.UUID(as_uuid=False), nullable=True))
    op.add_column('invoice', sa.Column('costed_amount', sa.Numeric(precision=15, scale=4), nullable=True))
    op.create_foreign_key(op.f('fk_invoice_costing_id_costing'), 'invoice', 'costing', ['costing_id'], ['costing_id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint(op.f('fk_invoice_costing_id_costing'), 'invoice', type_='foreignkey')
    op.drop_column('invoice', 'costed_amount')
    op.drop_column('invoice', 'costing_id')
