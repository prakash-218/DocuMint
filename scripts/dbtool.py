"""
Database chores.

    python scripts/dbtool.py migrate            # apply migrations (alembic upgrade head)
    python scripts/dbtool.py reset              # DROP everything, migrate  (refuses on Railway production)
    python scripts/dbtool.py demo               # reset + load the TechFlow demo data (tests/fixtures/demo.json)

The database is DATABASE_URL (default: local Docker Postgres on port 5434).
"""

import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import Boolean, Date, Numeric, create_engine, text  # noqa: E402
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP  # noqa: E402

from db import database_url  # noqa: E402
from store import schema  # noqa: E402

FIXTURE = ROOT / 'tests' / 'fixtures' / 'demo.json'
LOAD_ORDER = ['organization', 'users', 'user_organization', 'customer', 'contact', 'customer_user',
              'template', 'section', 'field', 'invoice', 'invoice_value', 'payment']


def migrate(url=None):
    from alembic import command
    from alembic.config import Config
    cfg = Config(str(ROOT / 'alembic.ini'))
    cfg.set_main_option('script_location', str(ROOT / 'alembic'))
    if url:
        os.environ['DATABASE_URL'] = url
    command.upgrade(cfg, 'head')


def reset(url=None):
    url = url or database_url()
    if os.getenv('RAILWAY_ENVIRONMENT_NAME') == 'production' and '--force' not in sys.argv:
        raise SystemExit('Refusing to reset the production database (pass --force if you really mean it).')
    engine = create_engine(url.replace('postgresql://', 'postgresql+psycopg://', 1) if url.startswith('postgresql://') else url)
    with engine.begin() as conn:
        conn.execute(text('DROP SCHEMA public CASCADE'))
        conn.execute(text('CREATE SCHEMA public'))
    engine.dispose()
    migrate(url)


def _convert(column, value):
    if value is None:
        return None
    t = column.type
    if isinstance(t, TIMESTAMP):
        return datetime.fromisoformat(value)
    if isinstance(t, Date):
        return date.fromisoformat(value[:10])
    if isinstance(t, Numeric):
        return Decimal(value)
    if isinstance(t, Boolean):
        return bool(value)
    if isinstance(t, JSONB):
        return value if not isinstance(value, str) else json.loads(value)
    return value


def load_fixture(url=None, path=FIXTURE):
    url = url or database_url()
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    engine = create_engine(url)
    with engine.begin() as conn:
        for name in LOAD_ORDER:
            table = schema.metadata.tables[name]
            rows = [{k: _convert(table.c[k], v) for k, v in r.items() if k in table.c} for r in data.get(name, [])]
            if rows:
                conn.execute(table.insert(), rows)
    engine.dispose()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'migrate'
    if cmd == 'migrate':
        migrate()
    elif cmd == 'reset':
        reset()
    elif cmd == 'demo':
        reset()
        load_fixture()
    else:
        raise SystemExit(__doc__)
    print('done')
