"""credit and debit notes

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-01 00:00:00

A document can be a credit note or a debit note: against a sent invoice, lowering or raising what it's owed. A credit
note can record money paid back (note_refund). Going back deletes notes and their refunds, since no other type can
hold them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0017'
down_revision: Union[str, None] = '0016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BEFORE = "doc_type IN ('quote', 'proforma', 'invoice', 'export_invoice', 'purchase_order')"
AFTER = "doc_type IN ('quote', 'proforma', 'invoice', 'export_invoice', 'purchase_order', 'credit_note', 'debit_note')"


def upgrade() -> None:
    op.drop_constraint(op.f('ck_invoice_doc_type'), 'invoice', type_='check')
    op.create_check_constraint(op.f('ck_invoice_doc_type'), 'invoice', AFTER)
    op.create_table('note_refund',
    sa.Column('refund_id', sa.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('invoice_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=4), nullable=False),
    sa.Column('refunded_on', sa.Date(), nullable=False),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('created_by', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('amount > 0', name=op.f('ck_note_refund_amount_positive')),
    sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('fk_note_refund_created_by_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.invoice_id'], name=op.f('fk_note_refund_invoice_id_invoice'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organization.org_id'], name=op.f('fk_note_refund_org_id_organization'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('refund_id', name=op.f('pk_note_refund'))
    )
    op.create_index(op.f('ix_note_refund_invoice_id'), 'note_refund', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_note_refund_org_id'), 'note_refund', ['org_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_note_refund_org_id'), table_name='note_refund')
    op.drop_index(op.f('ix_note_refund_invoice_id'), table_name='note_refund')
    op.drop_table('note_refund')
    op.execute("DELETE FROM invoice WHERE doc_type IN ('credit_note', 'debit_note')")
    op.drop_constraint(op.f('ck_invoice_doc_type'), 'invoice', type_='check')
    op.create_check_constraint(op.f('ck_invoice_doc_type'), 'invoice', BEFORE)
