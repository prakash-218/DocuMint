import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def fake_db(monkeypatch):
    import db as db_module
    from tests.fakedb import FakeDB

    fake = FakeDB()
    monkeypatch.setattr(db_module.db, 'execute_proc', fake.execute_proc)
    monkeypatch.setattr(db_module.db, 'execute_proc_single', fake.execute_proc_single)
    return fake


@pytest.fixture
def app(fake_db):
    from app import create_app

    app = create_app('testing')
    app.config.update(TESTING=True, SECRET_KEY='test-secret')
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login_as(client):
    def login(user_id, org_id, email='user@example.com'):
        with client.session_transaction() as s:
            s.clear()
            s.update(user_id=user_id, email=email, org_id=org_id)
    return login
