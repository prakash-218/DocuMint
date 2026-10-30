"""The React screens' side of Flask: the JSON API's login and refusals, and the built script on the pages."""

import json

import pytest

from tests.fakedb import ORG_A


@pytest.fixture
def owner(client, login_as):
    login_as('U-A', ORG_A, 'alice@a.com')
    return client


@pytest.mark.parametrize('role, can', [
    ('owner', {'edit': True, 'edit_customers': True, 'manage': True, 'read_mail': True, 'quotations_only': False}),
    ('member', {'edit': True, 'edit_customers': False, 'manage': False, 'read_mail': True, 'quotations_only': False}),
    ('viewer', {'edit': False, 'edit_customers': False, 'manage': False, 'read_mail': False, 'quotations_only': False}),
    ('sales', {'edit': True, 'edit_customers': True, 'manage': False, 'read_mail': False, 'quotations_only': True}),
])
def test_me_says_what_the_role_can_do(owner, fake_db, role, can):
    import permissions
    fake_db.members['U-A'][0]['role'] = role
    response = owner.get('/api/me')
    assert response.status_code == 200
    assert response.get_json() == {'email': 'alice@a.com', 'role': role, 'org': {'id': ORG_A, 'name': 'Org A'}, 'can': can,
                                   'permissions': sorted(permissions.ROLES[role])}


def test_refusals_are_json_not_redirects(client, login_as):
    response = client.get('/api/me')
    assert response.status_code == 401 and response.get_json() == {'error': 'Sign in first'}
    login_as('U-A', 'c' * 36)                       # an organization they're not in
    response = client.get('/api/me')
    assert response.status_code == 403 and 'not a member' in response.get_json()['error']
    response = client.get('/api/nothing-here')
    assert response.status_code == 404 and response.get_json() == {'error': 'Not found'}


def test_pages_still_redirect(client):
    response = client.get('/customers/')
    assert response.status_code == 302 and '/auth/login' in response.headers['Location']


def test_pages_load_the_built_script_when_there_is_one(app, owner, tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'static_folder', str(tmp_path / 'not-built'))
    assert '/static/app/' not in owner.get('/customers/').get_data(as_text=True)    # no build: nothing to load
    manifest = tmp_path / 'app' / '.vite' / 'manifest.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({'src/main.tsx': {'file': 'assets/main-abc123.js', 'css': ['assets/main-def456.css'],
                                                     'isEntry': True}}))
    monkeypatch.setattr(app, 'static_folder', str(tmp_path))
    html = owner.get('/customers/').get_data(as_text=True)
    assert '<script type="module" src="/static/app/assets/main-abc123.js"></script>' in html
    assert '<link rel="stylesheet" href="/static/app/assets/main-def456.css">' in html

