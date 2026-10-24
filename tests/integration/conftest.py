"""
Integration tests run against a real PostgreSQL database that is wiped and reloaded
with the demo data at the start of the session. Opt in with DOCUMINT_INTEGRATION_DB=1
and point DATABASE_URL at a throwaway database whose name contains "test":

    docker run -d --name documint-pg -e POSTGRES_PASSWORD=dev -p 5434:5432 postgres:16-alpine
    docker exec documint-pg psql -U postgres -c "CREATE DATABASE documint_test"
    DOCUMINT_INTEGRATION_DB=1 DATABASE_URL=postgresql+psycopg://postgres:dev@127.0.0.1:5434/documint_test pytest
"""

import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope='session', autouse=True)
def fresh_database(tmp_path_factory):
    if os.getenv('DOCUMINT_INTEGRATION_DB') != '1':
        yield
        return
    from db import database_url, db
    url = database_url()
    if 'test' not in url.rsplit('/', 1)[-1]:
        pytest.exit(f'Refusing to wipe {url}: the database name must contain "test"')
    os.environ.setdefault('STORAGE_DIR', str(tmp_path_factory.mktemp('storage')))
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
    import dbtool
    db.reset()
    dbtool.reset(url)
    dbtool.load_fixture(url)
    yield
    db.reset()
