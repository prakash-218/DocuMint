"""what arrived on a purchase order

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-31 22:00:00

What arrived on a purchase order (po_receipt): each delivery, with its date, the supplier's challan no. and how much
of each line came. Going back drops them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0016'
down_revision: Union[str, None] = '0015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('po_receipt',
    sa.Column('receipt_id', sa.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('invoice_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('received_on', sa.Date(), nullable=False),
    sa.Column('challan_no', sa.String(length=60), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('lines', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    sa.Column('created_by', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('fk_po_receipt_created_by_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.invoice_id'], name=op.f('fk_po_receipt_invoice_id_invoice'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organization.org_id'], name=op.f('fk_po_receipt_org_id_organization'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('receipt_id', name=op.f('pk_po_receipt'))
    )
    op.create_index(op.f('ix_po_receipt_invoice_id'), 'po_receipt', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_po_receipt_org_id'), 'po_receipt', ['org_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_po_receipt_org_id'), table_name='po_receipt')
    op.drop_index(op.f('ix_po_receipt_invoice_id'), table_name='po_receipt')
    op.drop_table('po_receipt')
