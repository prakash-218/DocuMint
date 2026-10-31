"""invites and password resets

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-31 19:00:00

Getting in is by invitation only: invite (an address, into an organization as a role, or to start a new one) and
password_reset (a link to set a new password). Both keep only their token's hash. An organization's domain may be
empty, since a public one (gmail.com) is never an organization's. Going back gives empty domains a placeholder.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0013'
down_revision: Union[str, None] = '0012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('password_reset',
    sa.Column('reset_id', sa.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('created_by', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('used_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('fk_password_reset_created_by_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name=op.f('fk_password_reset_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('reset_id', name=op.f('pk_password_reset')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_password_reset_token_hash'))
    )
    op.create_index(op.f('ix_password_reset_user_id'), 'password_reset', ['user_id'], unique=False)
    op.create_table('invite',
    sa.Column('invite_id', sa.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=20), server_default='member', nullable=False),
    sa.Column('role_id', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('created_by', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('used_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('used_by', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('cancelled_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('fk_invite_created_by_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['org_id'], ['organization.org_id'], name=op.f('fk_invite_org_id_organization'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['org_role.role_id'], name=op.f('fk_invite_role_id_org_role'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['used_by'], ['users.user_id'], name=op.f('fk_invite_used_by_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('invite_id', name=op.f('pk_invite')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_invite_token_hash'))
    )
    op.create_index(op.f('ix_invite_org_id'), 'invite', ['org_id'], unique=False)
    op.alter_column('organization', 'domain',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)


def downgrade() -> None:
    op.execute("UPDATE organization SET domain = 'none.invalid' WHERE domain IS NULL")
    op.alter_column('organization', 'domain',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.drop_index(op.f('ix_invite_org_id'), table_name='invite')
    op.drop_table('invite')
    op.drop_index(op.f('ix_password_reset_user_id'), table_name='password_reset')
    op.drop_table('password_reset')
