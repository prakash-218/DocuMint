"""payment terms

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-29 12:00:00

How many days after the invoice date a customer pays (None: their parent company's terms, else the
organization's usual ones, in the business profile). Invoices that have no due date of their own are
tracked as due that many days after their date (payment_terms.py); nothing is written on them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0010'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('customer', sa.Column('payment_days', sa.Integer(), nullable=True))
    op.create_check_constraint(op.f('ck_customer_payment_days'), 'customer', 'payment_days BETWEEN 0 AND 365')


def downgrade() -> None:
    op.drop_constraint(op.f('ck_customer_payment_days'), 'customer', type_='check')
    op.drop_column('customer', 'payment_days')
