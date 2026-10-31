"""purchase orders

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-31 21:00:00

A document can be a purchase order: what we buy, to a supplier, for a project or not. Going back deletes purchase
orders, since no other type can hold them.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0015'
down_revision: Union[str, None] = '0014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BEFORE = "doc_type IN ('quote', 'proforma', 'invoice', 'export_invoice')"
AFTER = "doc_type IN ('quote', 'proforma', 'invoice', 'export_invoice', 'purchase_order')"


def upgrade() -> None:
    op.drop_constraint(op.f('ck_invoice_doc_type'), 'invoice', type_='check')
    op.create_check_constraint(op.f('ck_invoice_doc_type'), 'invoice', AFTER)


def downgrade() -> None:
    op.execute("DELETE FROM invoice WHERE doc_type = 'purchase_order'")
    op.drop_constraint(op.f('ck_invoice_doc_type'), 'invoice', type_='check')
    op.create_check_constraint(op.f('ck_invoice_doc_type'), 'invoice', BEFORE)
