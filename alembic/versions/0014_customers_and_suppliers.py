"""customers and suppliers

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-31 20:00:00

Who a company is to us: a customer (we sell to it), a supplier (we buy from it, on purchase orders) or both. Every
company there is stays a customer; a site is what its company is.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0014'
down_revision: Union[str, None] = '0013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('customer', sa.Column('is_customer', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('customer', sa.Column('is_supplier', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('customer', 'is_supplier')
    op.drop_column('customer', 'is_customer')
