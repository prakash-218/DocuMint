"""
Custom roles end to end against real PostgreSQL (same opt-in as test_app_db.py): the owner makes a role, gives it to a
teammate, who then has exactly its permissions; changing the role changes what they may do at once; a role in use
can't be deleted; the audit log and notifications follow it.
"""

from tests.integration.test_documents_db import app, client, gst_org  # noqa: F401
from tests.integration.test_app_db import OWNER, VIEWER, login, pytestmark  # noqa: F401


def _user_id(email):
    from db import db
    return db.execute_proc_single('sp_get_user_by_email', (email,))['user_id']


def _give(client, email, role):
    response = client.post('/settings/members/approve', data={'user_id': _user_id(email), 'action': 'change_role', 'role': role})
    assert response.status_code == 302


def test_a_custom_role_end_to_end(client, gst_org):
    from db import db
    org_id = gst_org
    response = client.post('/api/settings/roles', json={'name': 'Estimator', 'description': 'Prices jobs',
                                                       'permissions': ['quotes.write', 'costings.write', 'projects.read',
                                                                       'notifications.read']})
    assert response.status_code == 201, response.get_json()
    role_id = response.get_json()['id']
    role = db.execute_proc_single('sp_get_role', (org_id, role_id))
    assert role['permissions'] == ['costings.read', 'costings.write', 'notifications.read', 'projects.read', 'quotes.read', 'quotes.write']
    assert client.post('/api/settings/roles', json={'name': 'Estimator', 'permissions': []}).status_code == 409

    _give(client, VIEWER, role_id)
    try:
        member = next(m for m in db.execute_proc('sp_get_org_members', (org_id,)) if m['email'] == VIEWER)
        assert (member['role'], str(member['role_id']), member['role_name']) == ('custom', role_id, 'Estimator')
        log = db.execute_proc('sp_get_audit_log', (org_id, 'user_organization', 10, 0))
        assert any(e['old_value'] == 'viewer' and e['new_value'] == 'Estimator' for e in log)

        # What happens on a project reaches them: the role gets notified
        db.execute_proc('sp_record_event', (org_id, None, 'note', 'A note for the team', None, None, _user_id(OWNER)))
        notified = db.execute_proc('sp_list_notifications', (_user_id(VIEWER), org_id, 5, True)) or []
        assert any(n['title'] == 'A note for the team' for n in notified)

        # They have the role's permissions, and nothing else
        login(client, VIEWER)
        me = client.get('/api/me').get_json()
        assert (me['role'], me['role_label']) == ('custom', 'Estimator') and 'costings.write' in me['permissions']
        assert client.get('/quotes/').status_code == 200 and client.get('/costings/rates').status_code == 200
        assert client.get('/invoices/').status_code == 302 and client.get('/api/customers').status_code == 403
        assert client.get('/api/settings/roles').status_code == 403

        # The owner takes costings out of the role: gone for them at once
        login(client, OWNER)
        response = client.patch(f'/api/settings/roles/{role_id}', json={'name': 'Estimator', 'description': 'Prices jobs',
                                                                      'permissions': ['quotes.write', 'projects.read']})
        assert response.status_code == 200
        assert any(e['field_name'] == 'permissions' and 'costings.write' in (e['old_value'] or '')
                   for e in db.execute_proc('sp_get_audit_log', (org_id, 'org_role', 10, 0)))
        login(client, VIEWER)
        assert client.get('/costings/rates').status_code == 403 and client.get('/quotes/').status_code == 200

        # A role someone has can't go
        login(client, OWNER)
        response = client.delete(f'/api/settings/roles/{role_id}', json={})
        assert response.status_code == 409 and '1 person has this role' in response.get_json()['error']
    finally:
        login(client, OWNER)
        _give(client, VIEWER, 'viewer')
    assert client.delete(f'/api/settings/roles/{role_id}', json={}).status_code == 200
    assert db.execute_proc_single('sp_get_role', (org_id, role_id)) is None
