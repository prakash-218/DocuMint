import json

import pytest

from tests.fakedb import ORG_A, ORG_B, PASSWORD


def test_nobody_signs_up_without_an_invite(client):
    from tests.spa import boot_of
    page = boot_of(client.post('/auth/register', data={'email': 'stranger@gmail.com'}).get_data(as_text=True))
    assert page['screen'] == 'invite_only'                                   # it only says how to get in
    for path in ('/auth/register/verify', '/auth/register/select-org', '/auth/register/org'):
        assert client.post(path, data={'email': 'alice@a.com', 'existing_user': 'true', 'org_id': ORG_A, 'domain': 'a.com',
                                       'password': PASSWORD, 'confirm_password': PASSWORD, 'org_name': 'Mine'}).status_code == 404
    with client.session_transaction() as s:
        assert s.get('user_id') is None
    assert client.get('/auth/invite/not-a-real-invite-token-0123456789abcdef').status_code == 404


@pytest.mark.parametrize('method,path', [
    ('get', '/invoices/INV-A'),
    ('get', '/invoices/INV-A/pdf'),
    ('post', '/invoices/INV-A/finalize'),
    ('post', '/invoices/INV-A/payment'),
    ('post', '/invoices/INV-A/delete'),
    ('get', '/templates/T-A'),
    ('post', '/templates/T-A/section/S-ITEMS/delete'),
    ('post', '/templates/T-A/field/F-QTY/delete'),
])
def test_other_org_is_blocked(client, login_as, fake_db, method, path):
    login_as('U-B', ORG_B)
    response = getattr(client, method)(path, data={'amount': '5'})
    assert response.status_code == 302
    assert fake_db.written() == []


def test_foreign_field_id_rejected_on_own_template(client, login_as, fake_db):
    login_as('U-A', ORG_A)
    client.post('/templates/T-A/field/F-SOMEONE-ELSE/delete')
    assert fake_db.written() == []
    client.post('/templates/T-A/field/F-QTY/delete')
    assert [c[0] for c in fake_db.written()] == ['sp_delete_field']


def test_role_change_applies_without_relogin(client, login_as, fake_db):
    login_as('U-A', ORG_A)
    fake_db.members['U-A'][0]['role'] = 'viewer'
    client.post('/templates/T-A/field/F-QTY/delete')
    assert fake_db.written() == []


def test_deactivated_member_sees_status_page(client, login_as, fake_db):
    login_as('U-A', ORG_A)
    fake_db.members['U-A'][0]['status'] = 'deactivated'
    response = client.get('/invoices/')
    assert b'deactivated' in response.data.lower()
    assert not any(c[0] == 'sp_list_invoices' for c in fake_db.calls)


def test_owner_cannot_deactivate_self(client, login_as, fake_db):
    login_as('U-A', ORG_A)
    client.post('/settings/members/approve', data={'user_id': 'U-A', 'action': 'deactivate'})
    assert fake_db.written() == []


def test_no_redirect_to_foreign_referer(client, login_as):
    login_as('U-A', ORG_A)
    response = client.post('/settings/members/approve', data={}, headers={'Referer': 'https://evil.example/x'})
    assert 'evil.example' not in response.headers['Location']


def test_production_requires_secret_key(monkeypatch):
    import config
    from app import create_app

    monkeypatch.setattr(config.ProductionConfig, 'SECRET_KEY', config.DEFAULT_SECRET_KEY)
    with pytest.raises(RuntimeError):
        create_app('production')
