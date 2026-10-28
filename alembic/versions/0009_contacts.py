"""contacts

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-28 21:30:00

Contacts at a customer, kept per organization (the old person table was shared by every
organization, one row per email address, and nothing wrote to it), what each contact gets on a
project, and what someone chose to ignore among the people found in a customer's emails.
Anything in the old tables is copied across before they go.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GETS = "gets IN ('all', 'billing', 'none')"


def upgrade() -> None:
    op.create_table('contact',
    sa.Column('contact_id', sa.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('customer_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=True),
    sa.Column('phone', sa.String(length=40), nullable=True),
    sa.Column('role', sa.String(length=100), nullable=True),
    sa.Column('gets', sa.String(length=10), server_default='all', nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint(GETS, name=op.f('ck_contact_gets')),
    sa.ForeignKeyConstraint(['customer_id'], ['customer.customer_id'], name=op.f('fk_contact_customer_id_customer'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organization.org_id'], name=op.f('fk_contact_org_id_organization'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('contact_id', name=op.f('pk_contact')),
    sa.UniqueConstraint('customer_id', 'email', name='uq_contact_customer_email')
    )
    op.create_index(op.f('ix_contact_customer_id'), 'contact', ['customer_id'], unique=False)
    op.create_index(op.f('ix_contact_org_id'), 'contact', ['org_id'], unique=False)
    op.create_table('contact_ignored',
    sa.Column('customer_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('value', sa.String(length=320), nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customer.customer_id'], name=op.f('fk_contact_ignored_customer_id_customer'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('customer_id', 'value', name=op.f('pk_contact_ignored'))
    )
    op.create_index(op.f('ix_contact_ignored_customer_id'), 'contact_ignored', ['customer_id'], unique=False)
    op.create_table('project_contact',
    sa.Column('project_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('contact_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('gets', sa.String(length=10), nullable=False),
    sa.CheckConstraint(GETS, name=op.f('ck_project_contact_gets')),
    sa.ForeignKeyConstraint(['contact_id'], ['contact.contact_id'], name=op.f('fk_project_contact_contact_id_contact'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['project.project_id'], name=op.f('fk_project_contact_project_id_project'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('project_id', 'contact_id', name=op.f('pk_project_contact'))
    )
    op.create_index(op.f('ix_project_contact_contact_id'), 'project_contact', ['contact_id'], unique=False)
    op.create_index(op.f('ix_project_contact_project_id'), 'project_contact', ['project_id'], unique=False)

    op.execute("""INSERT INTO contact (org_id, customer_id, name, email, role)
                  SELECT c.org_id, cca.customer_id, COALESCE(NULLIF(trim(p.full_name), ''), p.email), lower(p.email), cca.role
                  FROM customer_contact_assignment cca
                  JOIN person p ON p.person_id = cca.person_id
                  JOIN customer c ON c.customer_id = cca.customer_id
                  ON CONFLICT DO NOTHING""")
    op.drop_table('customer_contact_assignment')
    op.drop_table('person')


def downgrade() -> None:
    op.create_table('person',
    sa.Column('person_id', sa.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('person_id', name=op.f('pk_person')),
    sa.UniqueConstraint('email', name=op.f('uq_person_email'))
    )
    op.create_table('customer_contact_assignment',
    sa.Column('customer_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('person_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customer.customer_id'], name=op.f('fk_customer_contact_assignment_customer_id_customer'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['person_id'], ['person.person_id'], name=op.f('fk_customer_contact_assignment_person_id_person'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('customer_id', 'person_id', name=op.f('pk_customer_contact_assignment'))
    )
    op.create_index(op.f('ix_customer_contact_assignment_customer_id'), 'customer_contact_assignment', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customer_contact_assignment_person_id'), 'customer_contact_assignment', ['person_id'], unique=False)
    # Contacts with an email go back; phone numbers, what they get and ignored suggestions are lost
    op.execute("""INSERT INTO person (email, full_name)
                  SELECT DISTINCT ON (left(email, 255)) left(email, 255), left(name, 100) FROM contact
                  WHERE email IS NOT NULL ORDER BY left(email, 255), created_at
                  ON CONFLICT DO NOTHING""")
    op.execute("""INSERT INTO customer_contact_assignment (customer_id, person_id, role)
                  SELECT ct.customer_id, p.person_id, left(ct.role, 50) FROM contact ct JOIN person p ON p.email = left(ct.email, 255)
                  ON CONFLICT DO NOTHING""")
    op.drop_index(op.f('ix_project_contact_project_id'), table_name='project_contact')
    op.drop_index(op.f('ix_project_contact_contact_id'), table_name='project_contact')
    op.drop_table('project_contact')
    op.drop_index(op.f('ix_contact_ignored_customer_id'), table_name='contact_ignored')
    op.drop_table('contact_ignored')
    op.drop_index(op.f('ix_contact_org_id'), table_name='contact')
    op.drop_index(op.f('ix_contact_customer_id'), table_name='contact')
    op.drop_table('contact')
