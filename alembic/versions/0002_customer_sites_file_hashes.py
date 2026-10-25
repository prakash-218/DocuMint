"""customer sites; content hashes on files

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-25 01:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('customer', sa.Column('parent_id', sa.UUID(as_uuid=False), nullable=True))
    op.add_column('customer', sa.Column('site_name', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_customer_parent_id'), 'customer', ['parent_id'], unique=False)
    op.create_foreign_key(op.f('fk_customer_parent_id_customer'), 'customer', 'customer', ['parent_id'], ['customer_id'],
                          ondelete='RESTRICT')
    op.add_column('attachment', sa.Column('content_hash', sa.String(length=64), nullable=True))
    op.add_column('email_file', sa.Column('content_hash', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('email_file', 'content_hash')
    op.drop_column('attachment', 'content_hash')
    op.drop_constraint(op.f('fk_customer_parent_id_customer'), 'customer', type_='foreignkey')
    op.drop_index(op.f('ix_customer_parent_id'), table_name='customer')
    op.drop_column('customer', 'site_name')
    op.drop_column('customer', 'parent_id')
