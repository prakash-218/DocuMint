"""custom roles

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-30 02:00:00

An organization's own roles (org_role: a name and the permissions it grants), and a member can have
one: role 'custom' with its role_id. A role can't be deleted while someone has it. Going back first
makes anyone with a custom role a viewer.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0011'
down_revision: Union[str, None] = '0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('org_role',
    sa.Column('role_id', sa.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organization.org_id'], name=op.f('fk_org_role_org_id_organization'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('role_id', name=op.f('pk_org_role')),
    sa.UniqueConstraint('org_id', 'name', name='uq_org_role_name')
    )
    op.create_index(op.f('ix_org_role_org_id'), 'org_role', ['org_id'], unique=False)
    op.add_column('user_organization', sa.Column('role_id', sa.UUID(as_uuid=False), nullable=True))
    op.create_index(op.f('ix_user_organization_role_id'), 'user_organization', ['role_id'], unique=False)
    op.create_foreign_key(op.f('fk_user_organization_role_id_org_role'), 'user_organization', 'org_role', ['role_id'], ['role_id'], ondelete='RESTRICT')
    op.drop_constraint(op.f('ck_user_organization_role'), 'user_organization', type_='check')
    op.create_check_constraint(op.f('ck_user_organization_role'), 'user_organization',
                               "role IN ('owner', 'admin', 'member', 'viewer', 'sales', 'custom')")
    op.create_check_constraint(op.f('ck_user_organization_custom_role'), 'user_organization',
                               "(role = 'custom') = (role_id IS NOT NULL)")


def downgrade() -> None:
    op.execute("UPDATE user_organization SET role = 'viewer', role_id = NULL WHERE role = 'custom'")
    op.drop_constraint(op.f('ck_user_organization_custom_role'), 'user_organization', type_='check')
    op.drop_constraint(op.f('ck_user_organization_role'), 'user_organization', type_='check')
    op.create_check_constraint(op.f('ck_user_organization_role'), 'user_organization',
                               "role IN ('owner', 'admin', 'member', 'viewer', 'sales')")
    op.drop_constraint(op.f('fk_user_organization_role_id_org_role'), 'user_organization', type_='foreignkey')
    op.drop_index(op.f('ix_user_organization_role_id'), table_name='user_organization')
    op.drop_column('user_organization', 'role_id')
    op.drop_index(op.f('ix_org_role_org_id'), table_name='org_role')
    op.drop_table('org_role')
