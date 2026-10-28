"""sales role

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-28 18:00:00

A fifth role, sales: projects (and their files), quotations and customers, and nothing else
(auth.SALES_PAGES). Going back first makes anyone with it a viewer.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f('ck_user_organization_role'), 'user_organization', type_='check')
    op.create_check_constraint(op.f('ck_user_organization_role'), 'user_organization',
                               "role IN ('owner', 'admin', 'member', 'viewer', 'sales')")


def downgrade() -> None:
    op.execute("UPDATE user_organization SET role = 'viewer' WHERE role = 'sales'")
    op.drop_constraint(op.f('ck_user_organization_role'), 'user_organization', type_='check')
    op.create_check_constraint(op.f('ck_user_organization_role'), 'user_organization',
                               "role IN ('owner', 'admin', 'member', 'viewer')")
