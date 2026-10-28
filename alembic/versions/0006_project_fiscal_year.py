"""project fiscal year

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-27 20:40:00

A project's financial year ('26-27'): existing projects get the year of their earliest document,
or of the day they were started when they have none, in the organization's financial year
(April to March unless its profile says otherwise).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BACKFILL = """
WITH start AS (
    SELECT p.project_id,
           COALESCE((SELECT i.fiscal_year FROM invoice i
                      WHERE i.project_id = p.project_id AND i.fiscal_year IS NOT NULL
                      ORDER BY i.issue_date NULLS LAST, i.created_at LIMIT 1), '') AS doc_year,
           COALESCE((SELECT MIN(i.issue_date) FROM invoice i WHERE i.project_id = p.project_id),
                    p.created_at::date) AS day,
           CASE WHEN o.profile->>'fy_start_month' ~ '^[0-9]{1,2}$'
                     AND (o.profile->>'fy_start_month')::int BETWEEN 1 AND 12
                THEN (o.profile->>'fy_start_month')::int ELSE 4 END AS month
    FROM project p JOIN organization o ON o.org_id = p.org_id
), first_year AS (
    SELECT project_id, doc_year, month,
           CASE WHEN EXTRACT(MONTH FROM day) >= month THEN EXTRACT(YEAR FROM day)::int
                ELSE EXTRACT(YEAR FROM day)::int - 1 END AS y
    FROM start
)
UPDATE project p
   SET fiscal_year = CASE WHEN f.doc_year <> '' THEN f.doc_year
                          WHEN f.month = 1 THEN f.y::text
                          ELSE lpad((f.y % 100)::text, 2, '0') || '-' || lpad(((f.y + 1) % 100)::text, 2, '0') END
  FROM first_year f
 WHERE f.project_id = p.project_id
"""


def upgrade() -> None:
    op.add_column('project', sa.Column('fiscal_year', sa.String(length=7), nullable=True))
    op.execute(BACKFILL)
    op.alter_column('project', 'fiscal_year', nullable=False)


def downgrade() -> None:
    op.drop_column('project', 'fiscal_year')
