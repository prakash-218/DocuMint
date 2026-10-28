"""template used for

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-28 09:00:00

What each template is for (quotations, proformas, invoices), in its settings (template_layout.layout
'used_for'): the types of the documents already made with it, else what its name says, else any type.
Export invoices count as invoices (an invoice made with an export template is one).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ADD_MISSING = """
INSERT INTO template_layout (template_id, org_id, layout)
SELECT DISTINCT t.template_id, t.org_id, '{}'::jsonb FROM template t
 WHERE NOT EXISTS (SELECT 1 FROM template_layout l WHERE l.template_id = t.template_id)
"""

BACKFILL = """
UPDATE template_layout l
   SET layout = l.layout || jsonb_build_object('used_for', COALESCE(
        (SELECT jsonb_agg(DISTINCT CASE WHEN i.doc_type = 'export_invoice' THEN 'invoice' ELSE i.doc_type END)
           FROM invoice i WHERE i.template_id = l.template_id),
        (SELECT CASE WHEN position('proforma' IN lower(t.name)) > 0 THEN '["proforma"]'::jsonb
                     WHEN position('quot' IN lower(t.name)) > 0 THEN '["quote"]'::jsonb
                     WHEN position('invoice' IN lower(t.name)) > 0 THEN '["invoice"]'::jsonb
                     ELSE '[]'::jsonb END
           FROM template t WHERE t.template_id = l.template_id ORDER BY t.version DESC LIMIT 1),
        '[]'::jsonb))
 WHERE l.layout -> 'used_for' IS NULL
"""


def upgrade() -> None:
    op.execute(ADD_MISSING)
    op.execute(BACKFILL)


def downgrade() -> None:
    op.execute("UPDATE template_layout SET layout = layout - 'used_for'")
