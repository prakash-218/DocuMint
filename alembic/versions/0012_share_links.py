"""share links

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-31 18:00:00

Private links to a document (share_link): a long, unguessable token that opens the document's page and PDF
without signing in, for WhatsApp and copied links, until someone turns it off. At most one link per document
is on. Going back drops the links.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0012'
down_revision: Union[str, None] = '0011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('share_link',
    sa.Column('link_id', sa.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('invoice_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('token', sa.String(length=64), nullable=False),
    sa.Column('created_by', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('turned_off_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('opens', sa.Integer(), server_default='0', nullable=False),
    sa.Column('last_opened_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('fk_share_link_created_by_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.invoice_id'], name=op.f('fk_share_link_invoice_id_invoice'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organization.org_id'], name=op.f('fk_share_link_org_id_organization'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('link_id', name=op.f('pk_share_link')),
    sa.UniqueConstraint('token', name=op.f('uq_share_link_token'))
    )
    op.create_index(op.f('ix_share_link_invoice_id'), 'share_link', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_share_link_org_id'), 'share_link', ['org_id'], unique=False)
    op.create_index('uq_share_link_on', 'share_link', ['invoice_id'], unique=True,
                    postgresql_where=sa.text('turned_off_at IS NULL'))


def downgrade() -> None:
    op.drop_index('uq_share_link_on', table_name='share_link', postgresql_where=sa.text('turned_off_at IS NULL'))
    op.drop_index(op.f('ix_share_link_org_id'), table_name='share_link')
    op.drop_index(op.f('ix_share_link_invoice_id'), table_name='share_link')
    op.drop_table('share_link')
