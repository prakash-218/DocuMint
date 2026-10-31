"""
Invite-only against real PostgreSQL (same opt-in as test_app_db.py): an owner invites a Gmail address, it opens the
link and is in with that role; an account that exists signs in to accept; a custom role; who may invite whom; a
cancelled or used invite; the operator's invite to start an organization; and a password reset link.
"""

import re
import uuid

from tests.integration.test_app_db import OWNER, PASSWORD, VIEWER, app, client, login, org_of, pytestmark  # noqa: F401


def _token(link):
    return re.search(r'/auth/(?:invite|reset)/([A-Za-z0-9_-]{43})$', link).group(1)


def _screen(response):
    from tests.spa import boot_of
    return boot_of(response.get_data(as_text=True))


def _invite(client, email, role='member'):
    response = client.post('/api/settings/invites', json={'email': email, 'role': role})
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def _member(org_id, email):
    from db import db
    return next((m for m in db.execute_proc('sp_get_org_members', (org_id,)) or [] if m['email'] == email), None)


def test_a_gmail_address_gets_in_by_its_invite(app, client):
    login(client, OWNER)
    org_id = org_of(client)
    email = f'ravi.{uuid.uuid4().hex[:6]}@gmail.com'
    sent = _invite(client, email.upper())                                        # the address is kept in lower case
    assert sent['to'] == email and sent['emailed'] is False                       # no mailbox here: the link is to send
    token = _token(sent['link'])
    pending = client.get('/api/settings').get_json()['invites']
    assert any(i['email'] == email and i['role_label'] == 'Member' for i in pending)

    them = app.test_client()
    page = _screen(them.get(f'/auth/invite/{token}'))
    assert page['screen'] == 'accept_invite'
    assert {k: page['props'][k] for k in ('email', 'role', 'new_org', 'has_account', 'invited_by')} == \
        {'email': email, 'role': 'Member', 'new_org': False, 'has_account': False, 'invited_by': OWNER}
    assert them.post(f'/auth/invite/{token}', data={'password': 'short', 'confirm_password': 'short'}).status_code == 200   # refused
    done = them.post(f'/auth/invite/{token}', data={'password': 'gmailpass1', 'confirm_password': 'gmailpass1'})
    assert done.status_code == 302 and '/dashboard' in done.headers['Location']
    with them.session_transaction() as s:
        assert str(s['org_id']) == str(org_id) and s['email'] == email
    assert (_member(org_id, email)['role'], _member(org_id, email)['status']) == ('member', 'active')   # no approval needed
    assert app.test_client().get(f'/auth/invite/{token}').status_code == 410                         # once
    assert not any(i['email'] == email for i in client.get('/api/settings').get_json()['invites'])
    assert client.post('/api/settings/invites', json={'email': email}).status_code == 400            # in the team already


def test_an_account_that_exists_signs_in_to_accept_and_a_custom_role_sticks(app, client):
    from db import db
    from auth import hash_password
    login(client, OWNER)
    org_id = org_of(client)
    email = f'accounts.{uuid.uuid4().hex[:6]}@yahoo.com'
    db.execute_proc_single('sp_create_user', (email, hash_password('yahoopass1'), None))
    role = db.execute_proc_single('sp_save_role', (org_id, None, f'Billing {uuid.uuid4().hex[:4]}', 'Invoices only', ['invoices.read']))
    token = _token(_invite(client, email, str(role['role_id']))['link'])
    them = app.test_client()
    assert _screen(them.get(f'/auth/invite/{token}'))['props']['has_account'] is True
    assert them.post(f'/auth/invite/{token}', data={'password': 'wrong-pass'}).status_code == 200
    assert them.post(f'/auth/invite/{token}', data={'password': 'yahoopass1'}).status_code == 302
    joined = _member(org_id, email)
    assert (joined['role'], str(joined['role_id'])) == ('custom', str(role['role_id']))


def test_who_may_invite_whom_and_links_that_stop_working(app, client):
    login(client, VIEWER)
    assert client.post('/api/settings/invites', json={'email': 'x@gmail.com'}).status_code == 403   # viewers don't invite
    login(client, OWNER)
    assert client.post('/api/settings/invites', json={'email': 'not an address'}).status_code == 400
    email = f'later.{uuid.uuid4().hex[:6]}@gmail.com'
    first = _token(_invite(client, email)['link'])
    invite = next(i for i in client.get('/api/settings').get_json()['invites'] if i['email'] == email)
    again = _token(client.post(invite['again'], json={}).get_json()['link'])
    assert app.test_client().get(f'/auth/invite/{first}').status_code == 404              # sent again: the old link stops
    assert app.test_client().get(f'/auth/invite/{again}').status_code == 200
    assert client.delete(invite['cancel'], json={}).status_code == 200
    gone = app.test_client().get(f'/auth/invite/{again}')
    assert gone.status_code == 410 and _screen(gone)['props']['problem'] == 'cancelled'


def test_the_operator_invites_someone_to_start_an_organization(app):
    from scripts.dbtool import invite_org
    email = f'founder.{uuid.uuid4().hex[:6]}@gmail.com'
    with app.app_context():
        link = invite_org(email, 'http://localhost')
    token = _token(link)
    them = app.test_client()
    page = _screen(them.get(f'/auth/invite/{token}'))
    assert page['props']['new_org'] is True and page['props']['role'] == 'Owner'
    assert them.post(f'/auth/invite/{token}', data={'password': 'founder123', 'confirm_password': 'founder123'}).status_code == 200  # needs a name
    name = f'Founder Works {uuid.uuid4().hex[:4]}'
    assert them.post(f'/auth/invite/{token}', data={'password': 'founder123', 'confirm_password': 'founder123', 'org_name': name,
                                                    'state': 'Tamil Nadu', 'country': 'India'}).status_code == 302
    from db import db
    with them.session_transaction() as s:
        org_id = s['org_id']
        assert s['org_name'] == name
    org = next(o for o in db.execute_proc('sp_get_user_organizations', (db.execute_proc_single('sp_get_user_by_email', (email,))['user_id'],))
               if str(o['org_id']) == str(org_id))
    assert org['role'] == 'owner' and not org.get('domain')                                # gmail.com is nobody's domain
    assert db.execute_proc('sp_list_templates', (org_id, False))                           # starter templates to begin with


def test_a_reset_link_for_a_member_who_forgot(app, client):
    from db import db
    login(client, OWNER)
    org_id = org_of(client)
    email = f'forgetful.{uuid.uuid4().hex[:6]}@gmail.com'
    token = _token(_invite(client, email)['link'])
    app.test_client().post(f'/auth/invite/{token}', data={'password': 'firstpass1', 'confirm_password': 'firstpass1'})
    me = _member(org_id, email)
    member = next(m for m in client.get('/api/settings').get_json()['members'] if m['email'] == email)
    assert member['reset']
    sent = client.post(member['reset'], json={}).get_json()
    reset = _token(sent['link'])
    them = app.test_client()
    assert _screen(them.get(f'/auth/reset/{reset}'))['props']['email'] == email
    assert them.post(f'/auth/reset/{reset}', data={'password': 'newpass123', 'confirm_password': 'newpass123'}).status_code == 302
    assert them.get(f'/auth/reset/{reset}').status_code == 410                              # once
    assert them.post('/auth/login', data={'email': email, 'password': 'newpass123'}).status_code == 302
    # forgetting it without an owner: the same answer whether or not there's an account
    for address in (email, 'nobody-here@gmail.com'):
        page = _screen(app.test_client().post('/auth/forgot', data={'email': address}))
        assert page['screen'] == 'forgot' and page['props']['sent'] is True
    assert me['status'] == 'active'
